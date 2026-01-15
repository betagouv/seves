import datetime
import json
import logging
import typing
import unicodedata
from collections import defaultdict
from functools import cached_property, wraps
from typing import Mapping
from urllib.parse import urlencode

from celery.exceptions import OperationalError
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms import Media
from django.forms.utils import RenderableMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import BaseCreateView
from docxtpl import DocxTemplate, RichText
from queryset_sequence import QuerySetSequence

from core.forms import (
    AgentAddForm,
    DocumentEditForm,
    DocumentUploadForm,
    StructureAddForm,
)
from core.models import (
    Contact,
    Document,
    Export,
    FinSuiviContact,
    LienLibre,
    Message,
    Structure,
    User,
    Visibilite,
    user_is_referent_national,
)
from .constants import BSV_STRUCTURE, MUS_STRUCTURE
from .filters import DocumentFilter, MessageFilter
from .notifications import notify_message, notify_object_cloture
from .redirect import safe_redirect
from .validators import MAX_UPLOAD_SIZE_MEGABYTES, AllowedExtensions

if typing.TYPE_CHECKING:
    from .formsets import DocumentInMessageUploadFormSet

logger = logging.getLogger(__name__)


class MediaDefiningMixin(ContextMixin):
    def __new__(cls):
        """
        Wrapping get_context_data in a decorator here ensures get_media is called at the very last moment
        when all superclasses' get_context_data have been called.
        """

        def patch_get_context_data(get_context_data):
            @wraps(get_context_data)
            def wrapper(*args, **kwargs):
                context = get_context_data(*args, **kwargs)
                context.setdefault("media", obj.get_media(**context))
                return context

            return wrapper

        obj = super().__new__(cls)
        obj.get_context_data = patch_get_context_data(obj.get_context_data)
        return obj

    def get_media(self, **context_data) -> Media:
        return context_data["form"].media if "form" in context_data else Media()


class WithDocumentUploadFormMixin:
    def get_object_linked_to_document(self):
        raise NotImplementedError

    def get_redirect_url_after_upload(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["document_form"] = DocumentUploadForm(obj=obj, next=obj.get_absolute_url())
        context["allowed_extensions"] = AllowedExtensions.values
        context["max_upload_size_mb"] = MAX_UPLOAD_SIZE_MEGABYTES
        return context


class WithDocumentListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = Document.objects.for_fiche(self.get_object()).prefetch_related("created_by_structure")
        document_filter = DocumentFilter(self.request.GET, queryset=documents)
        for document in document_filter.qs:
            document.edit_form = DocumentEditForm(instance=document)
        context["document_filter"] = document_filter
        return context


class WithBlocCommunPermission:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["can_add_document"] = obj.can_add_document(self.request.user)
        context["can_update_document"] = obj.can_update_document(self.request.user)
        context["can_delete_document"] = obj.can_delete_document(self.request.user)
        context["can_download_document"] = obj.can_download_document(self.request.user)
        context["can_add_agent"] = obj.can_add_agent(self.request.user)
        context["can_add_structure"] = obj.can_add_structure(self.request.user)
        context["can_delete_contact"] = obj.can_delete_contact(self.request.user)
        return context


class WithMessageMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message_list = self.get_object().messages.for_user(self.request.user).optimized_for_list()
        message_filter = MessageFilter(self.request.GET, queryset=message_list)
        for message in message_filter.qs:
            message.can_be_deleted = message.can_user_delete(self.request.user)
        context["message_filter"] = message_filter
        context["message_status"] = Message.Status
        context["message_content_type"] = ContentType.objects.get_for_model(Message)
        context["can_add_di"] = self.request.user.agent.structure.is_ac
        context["can_add_cr_di"] = not self.request.user.agent.structure.is_ac
        return context


class WithContactFormsInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        content_type = ContentType.objects.get_for_model(obj)
        initial_data = {"content_id": obj.id, "content_type_id": content_type.id}
        context["add_contact_structure_form"] = StructureAddForm(initial=initial_data, obj=obj)
        context["add_contact_agent_form"] = AgentAddForm(initial=initial_data, obj=obj)
        return context


class WithContactQuerysetMixin:
    def get_agents(self, obj):
        return obj.contacts.agents_only().prefetch_related("agent__structure").order_by_structure_and_name()

    def get_structures(self, obj):
        return obj.contacts.structures_only().order_by("structure__libelle").select_related("structure")


class WithContactListInContextMixin(WithContactQuerysetMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        structures_fin_suivi_ids = (
            Structure.objects.filter(contact__finsuivicontact__in=obj.fin_suivi.all())
            .values_list("id", flat=True)
            .distinct()
        )

        context["contacts_agents"] = [
            {
                "contact": contact,
                "is_in_fin_suivi": contact.agent.structure_id in structures_fin_suivi_ids,
            }
            for contact in self.get_agents(obj)
        ]

        context["contacts_structures"] = [
            {
                "contact": contact,
                "is_in_fin_suivi": contact.structure_id in structures_fin_suivi_ids,
                "email": contact.get_email_for_object(obj),
            }
            for contact in self.get_structures(obj)
        ]

        context["content_type"] = ContentType.objects.get_for_model(obj)
        return context


class WithFreeLinksListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["free_links_list"] = LienLibre.objects.for_object(self.get_object())
        return context


class IsActiveMixin(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AllowACNotificationMixin(models.Model):
    is_ac_notified = models.BooleanField(default=False)

    def can_notifiy(self, user):
        return not self.is_ac_notified and not (self.is_draft or self.is_cloture) and not user.agent.structure.is_ac

    def _add_bsv_and_mus_to_contacts(self):
        bsv_contact = Contact.objects.get(structure__niveau2=BSV_STRUCTURE)
        mus_contact = Contact.objects.get(structure__niveau2=MUS_STRUCTURE)
        self.contacts.add(bsv_contact, mus_contact)

    def notify_ac(self, user):
        if not self.can_notifiy(user):
            raise ValidationError("Vous ne pouvez pas notifier cet objet à l'AC")

        self.is_ac_notified = True
        message = Message(
            message_type=Message.NOTIFICATION_AC,
            title="Notification à l'AC",
            content="L'administration a été notifiée de cette fiche.",
            sender=user.agent.contact_set.get(),
            sender_structure=user.agent.structure,
            content_object=self,
        )

        try:
            notify_message(message)
            with transaction.atomic():
                self.save()
                message.save()
                self._add_bsv_and_mus_to_contacts()
        except ValidationError as e:
            raise ValidationError(f"Une erreur s'est produite lors de la notification : {e.message}")
        except OperationalError:
            logger.error("Could not connect to Redis")
            raise ValidationError("Une erreur s'est produite lors de l'envoi du message de notification.")

    class Meta:
        abstract = True


class WithMessageUrlsMixin:
    @property
    def add_message_url(self):
        content_type = ContentType.objects.get_for_model(self)
        return reverse("message-add", kwargs={"obj_type_pk": content_type.pk, "obj_pk": self.pk})


class WithVisibiliteMixin(models.Model):
    visibilite = models.CharField(
        max_length=100,
        choices=Visibilite,
        default=Visibilite.LOCALE,
    )
    allowed_structures = models.ManyToManyField(Structure, related_name="allowed_structures")

    class Meta:
        abstract = True

    @property
    def is_visibilite_nationale(self):
        return self.visibilite == Visibilite.NATIONALE

    @property
    def is_visibilite_limitee(self):
        return self.visibilite == Visibilite.LIMITEE

    @property
    def is_visibilite_locale(self):
        return self.visibilite == Visibilite.LOCALE

    def can_update_visibilite(self, user):
        raise NotImplementedError

    def can_user_access(self, user):
        """Vérifie si l'utilisateur peut accéder à la fiche de détection."""
        if self.is_visibilite_nationale:
            return True
        if user.agent.is_in_structure(self.createur):
            return True
        if not self.is_draft and (user.agent.structure.is_mus_or_bsv or user_is_referent_national(user)):
            return True
        if self.is_visibilite_limitee and not self.is_draft and user.agent.structure in self.allowed_structures.all():
            return True
        return False

    def get_visibilite_display_text(self) -> str:
        match self.visibilite:
            case Visibilite.LOCALE:
                return ", ".join({str(self.createur), MUS_STRUCTURE, BSV_STRUCTURE})
            case Visibilite.LIMITEE:
                return ", ".join(str(s) for s in self.allowed_structures.all()) + f", {MUS_STRUCTURE}, {BSV_STRUCTURE}"
            case Visibilite.NATIONALE:
                return "Toutes les structures"

    def update_allowed_structures_and_visibility(self, contacts_structures: list[Contact]):
        if not contacts_structures or self.is_visibilite_nationale:
            return
        structures = [contact.structure for contact in contacts_structures]
        self.allowed_structures.add(*structures)
        if self.is_visibilite_locale:
            self.visibilite = Visibilite.LIMITEE
            self.save()

    @property
    def visibility_display(self) -> str:
        return Visibilite.get_masculine_label(self.visibilite)

    def save(self, *args, **kwargs):
        if self.pk:
            if self.is_visibilite_limitee and self.allowed_structures.count() == 0:
                raise ValidationError("Vous ne pouvez pas avoir une visibilitée limitée sans structure sélectionnée.")
            if not self.is_visibilite_limitee and self.allowed_structures.count() != 0:
                raise ValidationError(
                    "Vous ne pouvez pas avoir des structures autorisée dans un autre cas que la visibilitée limitée."
                )
        super().save(*args, **kwargs)


class WithEtatMixin(models.Model):
    class Etat(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_COURS = "en_cours", "En cours"
        CLOTURE = "cloture", "Clôturé"

    etat = models.CharField(max_length=100, choices=Etat, verbose_name="État de l'événement", default=Etat.BROUILLON)

    class Meta:
        abstract = True

    def cloturer(self):
        self.etat = self.Etat.CLOTURE
        self.save()
        notify_object_cloture(self)

    def publish(self):
        self.etat = self.Etat.EN_COURS
        self.save()

    @property
    def is_draft(self):
        return self.etat == self.Etat.BROUILLON

    @property
    def is_cloture(self):
        return self.etat == self.Etat.CLOTURE

    @property
    def is_published(self):
        return self.etat == self.Etat.EN_COURS

    def can_publish(self, user):
        return user.agent.is_in_structure(self.createur) if self.is_draft else False

    def can_be_cloture_by(self, user):
        return user.agent.structure.is_ac

    def is_the_only_remaining_structure(self, user, contacts_not_in_fin_suivi) -> bool:
        """Un seul contact sans fin de suivi qui appartient à la structure de l'utilisateur"""
        return len(contacts_not_in_fin_suivi) == 1 and contacts_not_in_fin_suivi[0].structure == user.agent.structure

    def can_be_cloture(self, user) -> tuple[bool, str]:
        if self.is_draft:
            return False, "L'événement est en brouillon et ne peut pas être clôturé."
        if self.is_cloture:
            return False, f"L'événement n°{self.numero} est déjà clôturé."
        if not self.can_be_cloture_by(user):
            return False, "Vous n'avez pas les droits pour clôturer cet événement."
        return True, ""

    def can_ouvrir(self, user: User):
        """Vérifie si l'évènement peut être ouvert (repasser dans l'état EN COURS)"""
        if self.is_cloture:
            return user.agent.structure.is_ac
        return False

    def get_publish_success_message(self):
        return "Objet publié avec succès"

    def get_publish_error_message(self):
        return "Cet objet ne peut pas être publié"

    def get_etat_data_for_contact(self, contact):
        content_type = ContentType.objects.get_for_model(self)
        is_fin_de_suivi = FinSuiviContact.objects.filter(content_type=content_type, object_id=self.pk)
        is_fin_de_suivi = is_fin_de_suivi.filter(contact=contact).exists()
        return self.get_etat_data_from_fin_de_suivi(is_fin_de_suivi)

    def get_etat_data_from_fin_de_suivi(self, is_fin_de_suivi):
        if is_fin_de_suivi:
            return {"etat": "fin de suivi", "readable_etat": "Fin de suivi"}
        return {"etat": self.etat, "readable_etat": self.get_etat_display()}

    def get_cloture_confirm_message(self):
        return "L'objet a bien été cloturé."


class AllowModificationMixin(WithEtatMixin):
    def can_user_access(self, user):
        if user.agent.is_in_structure(self.createur):
            return True
        return not self.is_draft

    def can_be_modified(self, user):
        return self.can_user_access(user) and not self.is_cloture

    class Meta:
        abstract = True


class WithFreeLinkIdsMixin:
    @property
    def free_link_ids(self):
        content_type = ContentType.objects.get_for_model(self)
        links = LienLibre.objects.for_object(self).select_related("content_type_2", "content_type_1")
        link_ids = []
        for link in links:
            if link.object_id_1 == self.id and link.content_type_1 == content_type:
                link_ids.append(f"{link.content_type_2.pk}-{link.object_id_2}")
            else:
                link_ids.append(f"{link.content_type_1.pk}-{link.object_id_1}")
        return link_ids

    @property
    def free_link_ids_json(self):
        try:
            return json.dumps(self.free_link_ids)
        except Exception as e:
            logger.exception(e)
            return json.dumps([])


class CanUpdateVisibiliteRequiredMixin:
    """
    Mixin pour vérifier que l'utilisateur connecté a le droit de modifier la visibilité.
    """

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_update_visibilite(request.user):
            messages.error(request, "Vous n'avez pas les droits pour modifier la visibilité de cet objet.")
            return safe_redirect(self.object.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)


class GetFicheObjectMixin:
    @cached_property
    def fiche_objet(self):
        return self.get_fiche_object()

    def get_fiche_object(self):
        raise NotImplementedError("Vous devez implémenter la méthode `get_fiche_object` pour ce mixin.")


class PreventActionIfVisibiliteBrouillonMixin(GetFicheObjectMixin):
    """
    Mixin pour empêcher des actions sur des objets ayant la visibilité 'brouillon'.
    """

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_fiche_object()
        if obj.is_draft:
            messages.error(request, "Action impossible car la fiche est en brouillon")
            return safe_redirect(request.POST.get("next") or obj.get_absolute_url() or "/")

        return super().dispatch(request, *args, **kwargs)


class WithObjectFromContentTypeMixin:
    def _get_object_from_content_type(self, *, object_id, content_type_id):
        if hasattr(self, "_object"):
            return self._object

        content_type = ContentType.objects.get(pk=content_type_id)
        ModelClass = content_type.model_class()
        self._object = get_object_or_404(ModelClass, pk=object_id)
        return self._object


class EmailNotificationMixin:
    """Mixin pour les modèles qui peuvent être notifiés par email."""

    def get_email_subject(self):
        raise NotImplementedError


class WithFormErrorsAsMessagesMixin(FormView):
    def form_invalid(self, form):
        for _, errors in form.errors.as_data().items():
            for error in errors:
                if error.code == "blocking_error":
                    messages.error(self.request, error.message, extra_tags="blocking")
                else:
                    messages.error(self.request, error.message)
        return super().form_invalid(form)


class WithNumeroMixin(models.Model):
    numero_annee = models.IntegerField(verbose_name="Année")
    numero_evenement = models.IntegerField(verbose_name="Numéro")

    class Meta:
        abstract = True

    @classmethod
    def _get_annee_and_numero(cls):
        annee_courante = datetime.datetime.now().year
        last_fiche = (
            cls._base_manager.filter(numero_annee=annee_courante)
            .select_for_update()
            .order_by("-numero_evenement")
            .first()
        )
        numero_evenement = last_fiche.numero_evenement + 1 if last_fiche else 1
        return annee_courante, numero_evenement

    @property
    def numero(self):
        return f"{self.numero_annee}.{self.numero_evenement}"


class BasePermissionMixin:
    def _user_can_interact(self, user):
        raise NotImplementedError


class WithDocumentPermissionMixin(BasePermissionMixin):
    def can_add_document(self, user):
        return self._user_can_interact(user)

    def can_update_document(self, user):
        return self._user_can_interact(user)

    def can_delete_document(self, user):
        return self._user_can_interact(user)

    def can_download_document(self, user):
        return self.can_user_access(user)


class WithContactPermissionMixin(BasePermissionMixin):
    def can_add_agent(self, user):
        return self._user_can_interact(user)

    def can_add_structure(self, user):
        return self._user_can_interact(user)

    def can_delete_contact(self, user):
        return self._user_can_interact(user)


class WithAddUserContactsMixin:
    """Mixin pour ajouter automatiquement l'utilisateur courant et sa structure comme contacts."""

    def add_user_contacts(self, obj):
        """Ajoute l'utilisateur courant et sa structure comme contacts de l'objet."""
        agent = self.request.user.agent

        agent_contact = Contact.objects.get(agent=agent)
        obj.contacts.add(agent_contact)

        if structure_contact := agent_contact.get_structure_contact():
            obj.contacts.add(structure_contact)


class WithClotureContextMixin:
    """
    Mixin qui ajoute au contexte les informations relatives à la clôture d'un objet.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object = self.get_object()
        user = self.request.user
        context["contacts_not_in_fin_suivi"] = contacts_structures_not_in_fin_suivi = (
            object.get_contacts_structures_not_in_fin_suivi()
        )
        context["is_evenement_can_be_cloture"], _ = object.can_be_cloture(user)
        context["is_the_only_remaining_structure"] = object.is_the_only_remaining_structure(
            user, contacts_structures_not_in_fin_suivi
        )
        return context


class WithFinDeSuiviMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_fin_de_suivi_be_added"] = FinSuiviContact().can_add_fin_de_suivi(
            self.get_object(), self.request.user
        )
        context["can_fin_de_suivi_be_removed"] = FinSuiviContact().can_remove_fin_de_suivi(
            self.get_object(), self.request.user
        )
        return context


class WithPublishMixin:
    def publish(self, obj, request):
        if not obj.can_publish(request.user):
            messages.error(request, obj.get_publish_error_message())
            return False
        try:
            obj.publish()
            messages.success(request, obj.get_publish_success_message())
            return True
        except AttributeError:
            messages.error(request, obj.get_publish_error_message())
            return False


class WithACNotificationMixin:
    def notify_ac(self, obj, request):
        try:
            obj.notify_ac(user=request.user)
            messages.success(request, "L'administration centrale a été notifiée avec succès")
            return True
        except AttributeError:
            messages.error(request, "Ce type d'objet n'est pas compatible avec une notification à l'AC.")
            return False
        except ValidationError as e:
            messages.error(request, e.message)
            return False


class WithOrderingMixin:
    ORDER_DIR_ASC = "asc"
    ORDER_DIR_DESC = "desc"

    def get_ordering_fields(self):
        raise NotImplementedError

    def get_default_order_by(self):
        raise NotImplementedError

    def get_default_order_dir(self):
        return self.ORDER_DIR_DESC

    def setup_ordering(self):
        ordering_fields = self.get_ordering_fields()
        default_order_dir = self.get_default_order_dir()
        default_order_by = self.get_default_order_by()
        order_dir_param = self.request.GET.get("order_dir", default_order_dir)
        order_by_param = self.request.GET.get("order_by", default_order_by)
        self.order_dir = (
            order_dir_param if order_dir_param in [self.ORDER_DIR_ASC, self.ORDER_DIR_DESC] else default_order_dir
        )
        self.order_by = order_by_param if order_by_param in ordering_fields else default_order_by

    def get_ordering_prefix(self):
        return "-" if self.order_dir == self.ORDER_DIR_DESC else ""

    def get_ordering(self):
        self.setup_ordering()
        ordering_fields = self.get_ordering_fields()
        order_by_field = ordering_fields.get(self.order_by)
        prefix = self.get_ordering_prefix()
        if isinstance(order_by_field, tuple):
            return tuple([prefix + field for field in order_by_field])
        return prefix + order_by_field

    def apply_ordering(self, queryset):
        ordering = self.get_ordering()
        if isinstance(ordering, str):
            ordering = (ordering,)
        return queryset.order_by(*ordering, "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, "order_by"):
            context["current_order_by"] = self.order_by
        if hasattr(self, "order_dir"):
            context["current_order_dir"] = self.order_dir
        return context


class MessageHandlingMixin(WithAddUserContactsMixin, GetFicheObjectMixin, MediaDefiningMixin, BaseCreateView):
    def get_document_in_message_upload_formset(self, message, **kwargs) -> "DocumentInMessageUploadFormSet":
        from django.views.generic.edit import FormMixin

        from core.formsets import DocumentInMessageUploadFormSet

        form_kwargs = FormMixin.get_form_kwargs(self)
        form_kwargs.update(
            {
                "user": self.request.user,
                "message": message,
                "allowed_document_types": self.fiche_objet.get_allowed_document_types(),
                **kwargs,
            }
        )
        return DocumentInMessageUploadFormSet(**form_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["add_document_formset"] = self.get_document_in_message_upload_formset(message=context["form"].instance)
        context["fiche_objet"] = self.fiche_objet
        return context

    def get_media(self, **context_data) -> Media:
        return super().get_media(**context_data) + context_data["add_document_formset"].media

    def _is_internal_communication(self, structures):
        """
        Returns True if all contacts involved are part of the same structure
        """
        return len(structures) <= 1

    def _handle_visibilite_if_needed(self, message):
        if not hasattr(self.fiche_objet, "visibilite"):
            return

        structures = [c.structure for c in self.fiche_objet.contacts.structures_only()]

        if self._is_internal_communication(structures):
            return
        if self.fiche_objet.visibilite == Visibilite.LOCALE:
            with transaction.atomic():
                self.fiche_objet.allowed_structures.set(structures)
                self.fiche_objet.visibilite = Visibilite.LIMITEE
                self.fiche_objet.save()
        if self.fiche_objet.visibilite == Visibilite.LIMITEE:
            self.fiche_objet.allowed_structures.set(structures)

    def _add_contacts_to_object(self, message):
        """
        Ajoute les destinataires du message dans les contacts (agent et leur structure)
        N'ajoute pas la structure quand son seul représentant est un référent national.
        """
        structures_with_agents = defaultdict(list)

        for contact in message.recipients.all().union(message.recipients_copy.all()):
            self.fiche_objet.contacts.add(contact)
            if contact.agent:
                structures_with_agents[contact.agent.structure].append(contact)

        for structure, contacts_agents in structures_with_agents.items():
            all_referents_nationaux = all(user_is_referent_national(contact.agent.user) for contact in contacts_agents)
            add_structure = not all_referents_nationaux
            if add_structure and (structure := contacts_agents[0].get_structure_contact()):
                self.fiche_objet.contacts.add(structure)

    def handle_message_form(self, form):
        formset = self.get_document_in_message_upload_formset(message=form.instance)

        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, add_document_formset=formset))

        response = super().form_valid(form)
        self._add_contacts_to_object(form.instance)
        self.add_user_contacts(self.fiche_objet)
        self._handle_visibilite_if_needed(form.instance)
        formset.save()
        try:
            transaction.on_commit(lambda: notify_message(form.instance))
        except OperationalError:
            messages.error(
                self.request, "Une erreur s'est produite lors de l'envoi du message.", extra_tags="core messages"
            )
            logger.error("Could not connect to Redis")
        else:
            messages.success(self.request, "Le message a bien été ajouté.", extra_tags="core messages")
        return response


class WithCommonContextVars(RenderableMixin):
    extra_context = None

    def get_context(self):
        extra_context = self.extra_context if isinstance(self.extra_context, Mapping) else {}
        return {"COMMUNES_API": settings.COMMUNES_API, **extra_context, **super().get_context()}


class WithDocumentExportContextMixin(WithContactQuerysetMixin):
    def get_free_links_numbers(self):
        free_links = LienLibre.objects.for_object(self.object)
        free_links_numbers = []
        for link in free_links:
            if link.related_object_1 == self.object and link.related_object_2.is_deleted is False:
                free_links_numbers.append(str(link.related_object_2))
            if link.related_object_2 == self.object and link.related_object_1.is_deleted is False:
                free_links_numbers.append(str(link.related_object_1))
        return free_links_numbers

    def create_document_bloc_commun(self):
        obj = self.object
        messages = [m for m in obj.messages.filter(status=Message.Status.FINALISE)]
        sub_template = DocxTemplate("core/doc_templates/bloc_commun.docx")

        for message in messages:
            text = message.content.split("\n")
            rich_text = RichText()
            for i, line in enumerate(text):
                rich_text.add(line)
            message.rt_content = rich_text

        context = {
            "messages": messages,
            "agents": self.get_agents(obj),
            "structures": self.get_structures(obj),
            "documents": Document.objects.for_fiche(obj).prefetch_related("created_by_structure"),
        }
        sub_template.render(context)
        sub_doc_file = f"subdoc_{obj}.docx"
        sub_template.save(sub_doc_file)
        return sub_doc_file


def normalize(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def sort_tree(tree):
    tree.sort(key=lambda x: normalize(x["name"]))
    for node in tree:
        if node["children"]:
            sort_tree(node["children"])


class WithChoicesToJS:
    @classmethod
    def build_options(cls, sorted_results=False):
        def insert_node(path, value, tree):
            current_level = tree
            for label in path[:-1]:
                existing = next((n for n in current_level if n["name"] == label), None)
                if not existing:
                    existing = {"name": label, "value": value, "children": []}
                    current_level.append(existing)
                current_level = existing["children"]
            current_level.append({"name": path[-1], "value": value, "children": []})

        options = []
        for option in cls:
            if hasattr(option, "short_name"):
                path = [p.strip() for p in option.short_name.split(">")]
            else:
                path = [p.strip() for p in option.label.split(">")]
            insert_node(path, option.value, options)

        for option in options:
            if option["children"] != []:
                option["isGroupSelectable"] = False
                option["value"] = 2 * option["value"]  # We can pick it we just need a unique value for TreeselectJS

        if sorted_results:
            sort_tree(options)

        return options


class WithExportHeterogeneousQuerysetMixin:
    def get_export_task(self):
        raise NotImplementedError

    def get_success_url(self):
        raise NotImplementedError

    def post(self, request):
        queryset = self.get_queryset()
        serialized_queryset_sequence = []

        if isinstance(queryset, QuerySetSequence):
            for qs in queryset._querysets:
                serialized_queryset_sequence.append(Export.from_queryset(qs))
        else:
            serialized_queryset_sequence = [Export.from_queryset(queryset)]

        task = Export.objects.create(queryset_sequence=serialized_queryset_sequence, user=request.user)
        self.get_export_task().delay(task.id)
        messages.success(
            request, "Votre demande d'export a bien été enregistrée, vous receverez un mail quand le fichier sera prêt."
        )
        allowed_keys = list(self.filter.get_filters().keys()) + ["order_by", "order_dir"]
        allowed_params = {k: v for k, v in request.GET.items() if k in allowed_keys}
        return HttpResponseRedirect(f"{self.get_success_url()}?{urlencode(allowed_params)}")


class WithFormsetInvalidMixin:
    def formset_invalid(self, formset, msg_1, msg_2):
        messages.error(self.request, msg_1)
        for i, form in enumerate(formset):
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(self.request, f"{msg_2} #{i + 1} : '{field}': {error}")

        return self.render_to_response(self.get_context_data())

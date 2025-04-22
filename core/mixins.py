import base64
import datetime

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from requests import ConnectTimeout, ReadTimeout
from django.views.generic import FormView

from core.forms import (
    DocumentUploadForm,
    DocumentEditForm,
    MessageForm,
    MessageDocumentForm,
    StructureAddForm,
    AgentAddForm,
)
from .constants import BSV_STRUCTURE, MUS_STRUCTURE
from .filters import DocumentFilter
from core.models import (
    Document,
    LienLibre,
    Contact,
    Message,
    Visibilite,
    Structure,
    FinSuiviContact,
    user_is_referent_national,
)
from .notifications import notify_message
from .redirect import safe_redirect
from celery.exceptions import OperationalError
import logging

from .validators import MAX_UPLOAD_SIZE_MEGABYTES, AllowedExtensions

logger = logging.getLogger(__name__)


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


class WithMessagesListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message_list"] = (
            self.get_object()
            .messages.all()
            .select_related("sender__agent__structure")
            .prefetch_related(
                "recipients__agent",
                "recipients__structure",
                "recipients__agent__structure",
                "recipients_copy__agent",
                "recipients_copy__structure",
                "recipients_copy__agent__structure",
                "documents",
            )
        )
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


class WithMessageFormInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["message_form"] = MessageForm(
            sender=self.request.user,
            obj=obj,
            next=obj.get_absolute_url(),
        )
        context["add_document_form"] = MessageDocumentForm()
        context["allowed_extensions"] = AllowedExtensions.values
        context["max_upload_size_mb"] = MAX_UPLOAD_SIZE_MEGABYTES
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


class WithContactListInContextMixin:
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
            for contact in obj.contacts.agents_only().prefetch_related("agent__structure").order_by_structure_and_name()
        ]

        context["contacts_structures"] = [
            {
                "contact": contact,
                "is_in_fin_suivi": contact.structure_id in structures_fin_suivi_ids,
            }
            for contact in obj.contacts.structures_only().order_by("structure__libelle").select_related("structure")
        ]

        context["content_type"] = ContentType.objects.get_for_model(obj)
        return context


class WithFreeLinksListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["free_links_list"] = LienLibre.objects.for_object(self.get_object())
        return context


class AllowsSoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)

    def can_user_delete(self, user):
        raise NotImplementedError

    def can_be_deleted(self, user):
        return self.can_user_delete(user)

    def soft_delete(self, user):
        if not self.can_be_deleted(user):
            raise PermissionDenied
        self.is_deleted = True
        self.save()

    def get_soft_delete_success_message(self):
        return "L'objet a bien été supprimé"

    def get_soft_delete_permission_error_message(self):
        return "Vous n'avez pas les droits pour supprimer cet objet"

    def get_soft_delete_attribute_error_message(self):
        return "Ce type d'objet ne peut pas être supprimé"

    def get_soft_delete_confirm_title(self):
        return "Supprimer cet objet"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cet objet ?"

    class Meta:
        abstract = True


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

    def publish(self):
        self.etat = self.Etat.EN_COURS
        self.save()

    @property
    def is_draft(self):
        return self.etat == self.Etat.BROUILLON

    @property
    def is_cloture(self):
        return self.etat == self.Etat.CLOTURE

    def can_publish(self, user):
        return user.agent.is_in_structure(self.createur) if self.is_draft else False

    def can_be_cloturer_by(self, user):
        return user.agent.structure.is_ac

    def is_the_only_remaining_structure(self, user, contacts_not_in_fin_suivi) -> bool:
        """Un seul contact sans fin de suivi qui appartient à la structure de l'utilisateur"""
        return len(contacts_not_in_fin_suivi) == 1 and contacts_not_in_fin_suivi[0].structure == user.agent.structure

    def can_be_cloturer(self, user) -> tuple[bool, str]:
        if self.is_draft:
            return False, "L'événement est en brouillon et ne peut pas être clôturé."
        if self.is_cloture:
            return False, f"L'événement n°{self.numero} est déjà clôturé."
        if not self.can_be_cloturer_by(user):
            return False, "Vous n'avez pas les droits pour clôturer cet événement."
        return True, ""

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
        if not self.is_cloture and is_fin_de_suivi:
            return {"etat": "fin de suivi", "readable_etat": "Fin de suivi"}
        return {"etat": self.etat, "readable_etat": self.get_etat_display()}


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


class PreventActionIfVisibiliteBrouillonMixin:
    """
    Mixin pour empêcher des actions sur des objets ayant la visibilité 'brouillon'.
    """

    def get_fiche_object(self):
        raise NotImplementedError("Vous devez implémenter la méthode `get_fiche_object` pour ce mixin.")

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

    def get_absolute_url_with_message(self, message_id: int):
        return f"{self.get_absolute_url()}?message={message_id}"


class WithSireneTokenMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not (settings.SIRENE_CONSUMER_KEY and settings.SIRENE_CONSUMER_SECRET):
            return context
        basic_auth = f"{settings.SIRENE_CONSUMER_KEY}:{settings.SIRENE_CONSUMER_SECRET}"
        auth_header = base64.b64encode(basic_auth.encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
        }
        data = {"grant_type": "client_credentials", "validity_period": 60 * 60}

        try:
            response = requests.post("https://api.insee.fr/token", headers=headers, data=data, timeout=0.200)
            context["sirene_token"] = response.json()["access_token"]
        except (KeyError, ConnectionError, ConnectTimeout, ReadTimeout):
            pass

        return context


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
        return self._user_can_interact(user)


class WithContactPermissionMixin(BasePermissionMixin):
    def can_add_agent(self, user):
        return self._user_can_interact(user)

    def can_add_structure(self, user):
        return self._user_can_interact(user)

    def can_delete_contact(self, user):
        return self._user_can_interact(user)

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction
from django.urls import reverse

from core.forms import DocumentUploadForm, DocumentEditForm
from .constants import BSV_STRUCTURE, MUS_STRUCTURE
from .filters import DocumentFilter
from core.models import Document, LienLibre, Contact, Message, Visibilite, Structure
from .notifications import notify_message
from .redirect import safe_redirect


class WithDocumentUploadFormMixin:
    def get_object_linked_to_document(self):
        raise NotImplementedError

    def get_redirect_url_after_upload(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["document_form"] = DocumentUploadForm(obj=obj, next=obj.get_absolute_url())
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
            .prefetch_related(
                "recipients__structure", "recipients__agent", "recipients_copy", "sender__agent", "documents"
            )
        )
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
            for contact in obj.contacts.agents_only()
            .prefetch_related("agent__structure")
            .services_deconcentres_first()
            .order_by_structure_and_name()
        ]

        context["contacts_structures"] = [
            {
                "contact": contact,
                "is_in_fin_suivi": contact.structure_id in structures_fin_suivi_ids,
            }
            for contact in obj.contacts.structures_only()
            .services_deconcentres_first()
            .order_by_structure_and_niveau2()
            .select_related("structure")
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

    def soft_delete(self, user):
        if not self.can_user_delete(user):
            raise PermissionDenied
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True


class IsActiveMixin(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AllowACNotificationMixin(models.Model):
    is_ac_notified = models.BooleanField(default=False)

    @property
    def can_notifiy(self):
        return not self.is_ac_notified and not self.is_draft

    def _add_bsv_and_mus_to_contacts(self):
        bsv_contact = Contact.objects.get(structure__niveau2=BSV_STRUCTURE)
        mus_contact = Contact.objects.get(structure__niveau2=MUS_STRUCTURE)
        self.contacts.add(bsv_contact, mus_contact)

    def notify_ac(self, sender):
        if not self.can_notifiy:
            raise ValidationError("Cet objet est déjà notifié à l'AC")

        self.is_ac_notified = True
        message = Message(
            message_type=Message.NOTIFICATION_AC,
            title="Notification à l'AC",
            content="L'administration a été notifiée de cette fiche.",
            sender=sender,
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

    class Meta:
        abstract = True


class WithMessageUrlsMixin:
    def get_add_message_url(self, message_type):
        content_type = ContentType.objects.get_for_model(self)
        return reverse(
            "message-add", kwargs={"message_type": message_type, "obj_type_pk": content_type.pk, "obj_pk": self.pk}
        )

    @property
    def add_message_url(self):
        return self.get_add_message_url(Message.MESSAGE)

    @property
    def add_note_url(self):
        return self.get_add_message_url(Message.NOTE)

    @property
    def add_point_de_suivi_url(self):
        return self.get_add_message_url(Message.POINT_DE_SITUATION)

    @property
    def add_demande_intervention_url(self):
        return self.get_add_message_url(Message.DEMANDE_INTERVENTION)

    @property
    def add_compte_rendu_url(self):
        return self.get_add_message_url(Message.COMPTE_RENDU)

    @property
    def add_fin_suivi_url(self):
        return self.get_add_message_url(Message.FIN_SUIVI)


class AllowVisibiliteMixin(models.Model):
    visibilite = models.CharField(
        max_length=100,
        choices=[
            ("brouillon", "Vous seul pourrez voir la fiche et la modifier"),
            (
                "local",
                "Seul votre structure et l'administration centrale pourront consulter et modifier la fiche",
            ),
            ("national", "La fiche sera et modifiable par toutes les structures"),
        ],
        default=Visibilite.BROUILLON,
    )

    class Meta:
        abstract = True

    def can_update_visibilite(self, user):
        """Vérifie si l'utilisateur peut modifier la visibilité de la fiche de détection."""
        match self.visibilite:
            case Visibilite.BROUILLON:
                return user.agent.is_in_structure(self.createur)
            case _:
                return False

    def can_user_access(self, user):
        """Vérifie si l'utilisateur peut accéder à la fiche de détection."""
        match self.visibilite:
            case Visibilite.BROUILLON:
                return user.agent.is_in_structure(self.createur)
            case Visibilite.LOCAL:
                return user.agent.structure.is_mus_or_bsv or user.agent.is_in_structure(self.createur)
            case Visibilite.NATIONAL:
                return True
            case _:
                return False


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
        if obj.visibilite == Visibilite.BROUILLON:
            messages.error(request, "Action impossible car la fiche est en brouillon")
            return safe_redirect(request.POST.get("next") or obj.get_absolute_url() or "/")

        return super().dispatch(request, *args, **kwargs)

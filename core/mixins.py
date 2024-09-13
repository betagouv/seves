from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import models

from core.forms import DocumentUploadForm, DocumentEditForm
from .filters import DocumentFilter
from core.models import Document, LienLibre, Contact, Message, Visibilite
from .notifications import notify_message


class WithDocumentUploadFormMixin:
    def get_object_linked_to_document(self):
        raise NotImplementedError

    def get_redirect_url_after_upload(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object_linked_to_document()
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
        context["contacts_agents"] = (
            self.get_object()
            .contacts.agents_only()
            .prefetch_related("agent__structure")
            .services_deconcentres_first()
            .order_by_structure_and_name()
        )
        context["contacts_structures"] = (
            self.get_object()
            .contacts.structures_only()
            .services_deconcentres_first()
            .order_by_structure_and_niveau2()
            .select_related("structure")
        )
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        context["contacts_fin_suivi"] = Contact.objects.filter(finsuivicontact__in=self.get_object().fin_suivi.all())
        return context


class WithFreeLinksListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["free_links_list"] = LienLibre.objects.filter(
            (Q(content_type_1=ContentType.objects.get_for_model(obj), object_id_1=obj.id))
            | (Q(content_type_2=ContentType.objects.get_for_model(obj), object_id_2=obj.id))
        )
        return context


class AllowsSoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True


class AllowACNotificationMixin(models.Model):
    is_ac_notified = models.BooleanField(default=False)

    @property
    def can_notifiy(self):
        return not self.is_ac_notified

    def notify_ac(self, sender):
        if not self.can_notifiy:
            raise ValidationError("Cet objet est déjà notifié à l'AC")

        self.is_ac_notified = True
        message = Message.objects.create(
            message_type=Message.NOTIFICATION_AC,
            title="Notification à l'AC",
            content="L'administration a été notifiée de cette fiche.",
            sender=sender,
            content_object=self,
        )
        notify_message(message)
        self.save()

    class Meta:
        abstract = True


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

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db import models

from core.forms import DocumentUploadForm, DocumentEditForm
from .filters import DocumentFilter
from core.models import Document, LienLibre


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
            self.get_object().contacts.exclude(agent__isnull=True).prefetch_related("agent__structure")
        )
        context["contacts_structures"] = self.get_object().contacts.exclude(structure__isnull=True)
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
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

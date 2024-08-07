from django.contrib.contenttypes.models import ContentType

from core.forms import DocumentUploadForm, DocumentEditForm
from .filters import DocumentFilter
from core.models import Document


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
        context["contacts"] = self.get_object().contacts.prefetch_related("agent__structure")
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        return context

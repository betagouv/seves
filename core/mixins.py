from core.forms import DocumentUploadForm


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
        context["document_list"] = self.get_object().documents.all()
        return context
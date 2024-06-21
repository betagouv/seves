from core.forms import DocumentUploadForm


class WithDocumentUploadFormMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document_form"] = DocumentUploadForm()
        return context
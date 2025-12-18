from functools import cached_property

from django.forms import Media
from django.forms.models import BaseModelFormSet, modelformset_factory

from core.form_mixins import js_module
from core.forms import DocumentInMessageUploadForm
from core.models import Document


class DocumentInMessageUploadBaseFormSet(BaseModelFormSet):
    template_name = "core/form/document_in_message_uploads.html"

    @property
    def media(self):
        return super().media + Media(
            css={"all": ("core/form/document_in_message_uploads.css",)},
            js=(js_module("core/form/document_in_message_uploads.mjs"),),
        )

    @cached_property
    def documents_forms(self):
        if not self.message:
            return []

        from core.forms import MessageDocumentForm

        return [MessageDocumentForm(instance=d, object=self.obj, with_nom=True) for d in self.message.documents.all()]

    def __init__(self, data=None, files=None, auto_id="id_%s", prefix=None, queryset=None, *, initial=None, **kwargs):
        self.obj = kwargs.pop("obj", None)
        self.user = kwargs.pop("user", None)
        self.message = kwargs.pop("message", None)
        super().__init__(data, files, auto_id, prefix, queryset, initial=initial, **kwargs)

    def get_form_kwargs(self, index):
        return {**super().get_form_kwargs(index), "message": self.message, "obj": self.obj, "user": self.user}

    def get_queryset(self):
        return super().get_queryset().none()

    def save(self, commit=True):
        return super().save(commit)


DocumentInMessageUploadFormSet = modelformset_factory(
    Document,
    DocumentInMessageUploadForm,
    formset=DocumentInMessageUploadBaseFormSet,
    extra=0,
)

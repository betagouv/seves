from django.forms import BaseFormSet, Media, formset_factory
from django.forms.utils import ErrorList

from core.form_mixins import js_module
from core.forms import DocumentInMessageUploadForm


class DocumentInMessageUploadBaseFormSet(BaseFormSet):
    template_name = "core/form/document_in_message_uploads.html"

    def __init__(
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        form_kwargs=None,
        error_messages=None,
        obj=None,
    ):
        if obj:
            form_kwargs = form_kwargs or {}
            form_kwargs["obj"] = obj
        super().__init__(data, files, auto_id, prefix, initial, error_class, form_kwargs, error_messages)

    @property
    def media(self):
        return super().media + Media(
            css={"all": ("core/form/document_in_message_uploads.css",)},
            js=(js_module("core/form/document_in_message_uploads.mjs"),),
        )


DocumentInMessageUploadFormSet = formset_factory(
    DocumentInMessageUploadForm,
    formset=DocumentInMessageUploadBaseFormSet,
    extra=0,
)

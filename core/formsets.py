import json
from functools import cached_property

from django.forms import Media
from django.forms.models import BaseModelFormSet, modelformset_factory

from core.form_mixins import js_module
from core.forms import DocumentInMessageUploadForm
from core.models import Document
from core.validators import MAX_UPLOAD_SIZE_MEGABYTES, AllowedExtensions


class DocumentInMessageUploadBaseFormSet(BaseModelFormSet):
    template_name = "core/form/document_in_message_uploads.html"

    @property
    def media(self):
        return super().media + Media(
            css={"all": ("core/form/document_in_message_uploads.css",)},
            js=(js_module("core/form/document_in_message_uploads.mjs"),),
        )

    @property
    def max_upload_size_mb(self):
        return MAX_UPLOAD_SIZE_MEGABYTES

    @property
    def allowed_extensions(self):
        return AllowedExtensions.values

    @cached_property
    def allowed_extensions_per_document_type(self):
        result = Document.get_accept_attribute_per_document_type()
        result[""] = "." + ",.".join(self.allowed_extensions)
        return json.dumps(result)

    def __init__(
        self,
        user,
        message,
        allowed_document_types,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        queryset=None,
        *,
        initial=None,
        **kwargs,
    ):
        self.allowed_document_types = allowed_document_types
        self.user = user
        self.message = message
        super().__init__(data, files, auto_id, prefix, queryset, initial=initial, **kwargs)

    def get_form_kwargs(self, index):
        return {
            **super().get_form_kwargs(index),
            "allowed_document_types": self.allowed_document_types,
            "message": self.message,
            "user": self.user,
        }

    def get_queryset(self):
        return super().get_queryset().none() if not self.message.pk else self.message.documents.all()


DocumentInMessageUploadFormSet = modelformset_factory(
    Document, DocumentInMessageUploadForm, formset=DocumentInMessageUploadBaseFormSet, extra=0, can_delete=True
)

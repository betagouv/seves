import json

from django.forms.widgets import FileInput

from core.models import Document
from core.validators import MAX_UPLOAD_SIZE_BYTES


class RestrictedFileWidget(FileInput):
    def __init__(self, attrs=None):
        attrs = attrs or {}
        accept_per_document_type = Document.get_accept_format_per_document_type()
        attrs["accept"] = accept_per_document_type[Document.TypeDocument.ARRETE]
        attrs["data-accept-allowed-extensions"] = json.dumps(accept_per_document_type)
        attrs["data-max-size"] = MAX_UPLOAD_SIZE_BYTES
        super().__init__(attrs)

import json

from django.forms.widgets import FileInput

from core.models import Document
from core.validators import MAX_UPLOAD_SIZE_BYTES, AllowedExtensions


class RestrictedFileWidget(FileInput):
    def __init__(self, attrs=None):
        accept_allowed_extensions = {
            document_type: "." + ",.".join(extensions)
            for document_type, extensions in Document.ALLOWED_EXTENSIONS_PER_DOCUMENT_TYPE.items()
        }
        accept_allowed_extensions["default"] = "." + ",.".join(AllowedExtensions.values)
        attrs = attrs or {}
        attrs["accept"] = accept_allowed_extensions["default"]
        attrs["data-accept-allowed-extensions"] = json.dumps(accept_allowed_extensions)
        attrs["data-max-size"] = MAX_UPLOAD_SIZE_BYTES
        super().__init__(attrs)

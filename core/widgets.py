from django.forms.widgets import FileInput

from core.validators import AUTHORIZED_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES


class RestrictedFileWidget(FileInput):
    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs["accept"] = ",".join(f".{ext}" for ext in AUTHORIZED_EXTENSIONS)
        attrs["data-max-size"] = MAX_UPLOAD_SIZE_BYTES
        super().__init__(attrs)

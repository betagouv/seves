from django.forms.widgets import FileInput

from core.validators import AUTHORIZED_EXTENSIONS


class RestrictedFileWidget(FileInput):
    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs["accept"] = ",".join(f".{ext}" for ext in AUTHORIZED_EXTENSIONS)
        super().__init__(attrs)

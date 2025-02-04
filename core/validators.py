import magic
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


AUTHORIZED_EXTENSIONS = [
    "png",
    "jpg",
    "jpeg",
    "gif",
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "odt",
    "ods",
    "csv",
    "qgs",
    "qgz",
]

AUTHORIZED_MIME_TYPES = [
    "image/png",
    "image/jpeg",
    "image/gif",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.spreadsheet",
    "text/csv",
    "application/x-qgis",
    "application/x-qgis-project",
]


@deconstructible
class MagicMimeValidator:
    def __call__(self, file):
        file_mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)
        if file_mime not in AUTHORIZED_MIME_TYPES:
            raise ValidationError(f"Type de fichier non autorisé: {file_mime}")


def validate_upload_file(file):
    MagicMimeValidator()(file)

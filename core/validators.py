import magic
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.deconstruct import deconstructible

MAX_UPLOAD_SIZE_MEGABYTES = 15
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MEGABYTES * 1024 * 1024


class AllowedExtensions(models.TextChoices):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    GIF = "gif"
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"
    ODT = "odt"
    ODS = "ods"
    CSV = "csv"
    QGS = "qgs"
    QGZ = "qgz"
    TXT = "txt"
    EML = "eml"


class AllowedMimeTypes(models.TextChoices):
    IMAGE_PNG = "image/png"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_GIF = "image/gif"
    APPLICATION_PDF = "application/pdf"
    APPLICATION_MSWORD = "application/msword"
    APPLICATION_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    APPLICATION_XLS = "application/vnd.ms-excel"
    APPLICATION_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    APPLICATION_ODT = "application/vnd.oasis.opendocument.text"
    APPLICATION_ODS = "application/vnd.oasis.opendocument.spreadsheet"
    TEXT_CSV = "text/csv"
    APPLICATION_QGIS = "application/x-qgis"
    APPLICATION_QGIS_PROJECT = "application/x-qgis-project"
    TEXT_PLAIN = "text/plain"
    MESSAGE_RFC822 = "message/rfc822"


@deconstructible
class MagicMimeValidator:
    def __call__(self, file):
        file_mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)
        if file_mime not in AllowedMimeTypes.values:
            raise ValidationError(f"Type de fichier non autorisé: {file_mime}")


def validate_upload_file(file):
    MagicMimeValidator()(file)

import contextlib
import mimetypes
import re
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
        file.seek(0)
        file_mime = magic.from_buffer(file.read(), mime=True)
        if file_mime == "application/octet-stream" and magic.version() < 546:
            # There's a knwon bug with libmagic where MS Office documents (xslx, docx, etc.) are detected as
            # application/octet-stream. This is fixed in libmagic 5.46.
            # See https://bugs.astron.com/view.php?id=517
            with contextlib.suppress(Exception):
                file_mime = mimetypes.guess_type(file.name)[0]
        if file_mime not in AllowedMimeTypes.values:
            raise ValidationError(f"Type de fichier non autorisé: {file_mime}")


def validate_upload_file(file):
    MagicMimeValidator()(file)


def validate_numero_agrement(value):
    pattern = r"^\d{2,3}\.\d{2,3}\.\d{2,3}$"
    if not re.match(pattern, value):
        raise ValidationError(f"{value} n'est pas un format valide.")

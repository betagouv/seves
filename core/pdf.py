import io

from django.core.files.base import ContentFile
import pikepdf
from pikepdf.sanitize import remove_javascript


def strip_javascript_from_pdf(document):
    with document.file.open("rb") as f:
        pdf = pikepdf.Pdf.open(f)
        remove_javascript(pdf)
        buffer = io.BytesIO()
        pdf.save(buffer)
        pdf.close()

    storage = document.file.storage
    name = document.file.name
    storage.delete(name)
    storage.save(name, ContentFile(buffer.getvalue()))

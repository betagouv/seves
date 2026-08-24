import logging

from celery import shared_task

from core.antivirus import scan_document
from core.models import Document
from core.pdf import strip_javascript_from_pdf
from core.validators import AllowedMimeTypes

logger = logging.getLogger(__name__)


@shared_task
def scan_for_viruses(document_pk):
    logger.info(f"Will start scanning of {document_pk}")
    document = Document.objects.get(pk=document_pk)

    if document.mimetype == AllowedMimeTypes.APPLICATION_PDF:
        strip_javascript_from_pdf(document)

    is_infected = scan_document(document)
    if is_infected is not None:
        document.is_infected = is_infected
        document.save(update_fields=["is_infected"])
    logger.info(f"Will end scanning of {document_pk}")

import logging

from celery import shared_task

from core.antivirus import scan_document
from core.models import Document

logger = logging.getLogger(__name__)


@shared_task
def scan_for_viruses(document_pk):
    logger.info(f"Will start scanning of {document_pk}")
    document = Document.objects.get(pk=document_pk)
    is_infected = scan_document(document)
    if is_infected is not None:
        document.is_infected = scan_document(document)
        document.save(update_fields=["is_infected"])
    logger.info(f"Will end scanning of {document_pk}")

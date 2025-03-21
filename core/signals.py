from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save

from core.models import Document
from django.conf import settings

from .tasks import scan_for_viruses
from celery.exceptions import OperationalError
from django.db import transaction
import logging

from .validators import MagicMimeValidator

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Document)
def bypass_antivirus_scan_if_needed(sender, instance, **kwargs):
    if instance._state.adding is True and settings.BYPASS_ANTIVIRUS and settings.DEBUG:
        instance.is_infected = False


@receiver(pre_save, sender=Document)
def set_mimetype_on_create(sender, instance, **kwargs):
    if not instance.pk and not instance.mimetype and instance.file:
        validator = MagicMimeValidator()
        instance.mimetype = validator(instance.file)


def run_virus_scan(instance):
    try:
        scan_for_viruses.delay(instance.pk)
    except OperationalError:
        logger.error("Could not connect to Redis")


@receiver(post_save, sender=Document)
def scan_for_viruses_on_creation_if_needed(sender, instance, created, **kwargs):
    if created and not settings.BYPASS_ANTIVIRUS:
        transaction.on_commit(lambda: run_virus_scan(instance))

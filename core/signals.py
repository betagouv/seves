from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save

from core.models import Document
from django.conf import settings

from .tasks import scan_for_viruses


@receiver(pre_save, sender=Document)
def bypass_antivirus_scan_if_needed(sender, instance, **kwargs):
    if instance._state.adding is True and settings.BYPASS_ANTIVIRUS and settings.DEBUG:
        instance.is_infected = False


@receiver(post_save, sender=Document)
def scan_for_viruses_on_creation_if_needed(sender, instance, created, **kwargs):
    if created and not settings.BYPASS_ANTIVIRUS:
        scan_for_viruses.delay_on_commit(instance.pk)

from django.dispatch import receiver
from django.db.models.signals import pre_save

from core.models import Document
from django.conf import settings


@receiver(pre_save, sender=Document)
def bypass_antivirus_scan_if_needed(sender, instance, **kwargs):
    if instance._state.adding is True and settings.BYPASS_ANTIVIRUS and settings.DEBUG:
        instance.is_infected = False

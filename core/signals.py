import logging

import reversion
from celery.exceptions import OperationalError
from django.conf import settings
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_migrate, pre_delete
from django.dispatch import receiver

from core.models import Document, LienLibre, Message, FinSuiviContact
from .tasks import scan_for_viruses

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Document)
def bypass_antivirus_scan_if_needed(sender, instance, **kwargs):
    if instance._state.adding is True and settings.BYPASS_ANTIVIRUS and settings.ENVIRONMENT in ("test", "dev"):
        instance.is_infected = False


def run_virus_scan(instance):
    try:
        scan_for_viruses.delay(instance.pk)
    except OperationalError:
        logger.error("Could not connect to Redis")


@receiver(post_save, sender=Document)
def scan_for_viruses_on_creation_if_needed(sender, instance, created, **kwargs):
    if created and not settings.BYPASS_ANTIVIRUS:
        transaction.on_commit(lambda: run_virus_scan(instance))


@receiver(post_migrate)
def tiac_feature_flag(sender, app_config, **kwargs):
    if app_config.label == "waffle":
        from waffle import get_waffle_flag_model

        get_waffle_flag_model().objects.get_or_create(name="tiac", defaults={"everyone": None, "superusers": True})


@receiver([post_save], sender=LienLibre)
def link_added(sender, instance, **kwargs):
    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"Le lien '{str(instance.related_object_2)}' a été ajouté à la fiche")
            reversion.add_to_revision(instance.related_object_1)
        with reversion.create_revision():
            reversion.set_comment(f"Le lien '{str(instance.related_object_1)}' a été ajouté à la fiche")
            reversion.add_to_revision(instance.related_object_2)


@receiver([pre_delete], sender=LienLibre)
def link_deleted(sender, instance, **kwargs):
    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"Le lien '{str(instance.related_object_2)}' a été supprimé à la fiche")
            reversion.add_to_revision(instance.related_object_1)
        with reversion.create_revision():
            reversion.set_comment(f"Le lien '{str(instance.related_object_1)}' a été supprimé à la fiche")
            reversion.add_to_revision(instance.related_object_2)


@receiver([post_save], sender=Message)
def message_deleted(sender, instance: Message, **kwargs):
    if instance.is_deleted is True and instance._initial_is_deleted is False:
        with transaction.atomic():
            with reversion.create_revision():
                reversion.set_comment(
                    f"Le message de type '{instance.get_message_type_display()}' ayant pour titre {instance.title} a été supprimé"
                )
                reversion.add_to_revision(instance.content_object)


@receiver(post_save, sender=FinSuiviContact)
def fin_suivi_added(sender, instance, created, **kwargs):
    if created:
        with transaction.atomic():
            with reversion.create_revision():
                reversion.set_comment(f"La structure {instance.contact} a déclarée la fin de suivi sur cette fiche")
                reversion.add_to_revision(instance.content_object)

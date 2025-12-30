import logging

import reversion
from celery.exceptions import OperationalError
from django.conf import settings
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_migrate, pre_delete
from django.dispatch import receiver

from core.models import Document, LienLibre, Message, FinSuiviContact, CustomRevisionMetaData
from .diffs import create_manual_version
from .notifications import notify_message_deleted
from .tasks import scan_for_viruses

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Document)
def bypass_antivirus_scan_if_needed(sender, instance, **kwargs):
    if instance._state.adding is True and settings.BYPASS_ANTIVIRUS and settings.ENVIRONMENT in ("test", "dev"):
        instance.is_infected = False


def run_virus_scan(instance):
    try:
        logger.info(f"Will create task for document {instance.pk}")
        scan_for_viruses.delay(instance.pk)
    except OperationalError:
        logger.error("Could not connect to Redis")


@receiver(post_save, sender=Document)
def scan_for_viruses_on_creation_if_needed(sender, instance, created, **kwargs):
    logger.info(f"Will check if we need to scan document {instance.pk}")
    if created and not settings.BYPASS_ANTIVIRUS:
        transaction.on_commit(lambda: run_virus_scan(instance))


@receiver(post_migrate)
def tiac_feature_flag(sender, app_config, **kwargs):
    if app_config.label == "waffle":
        from waffle import get_waffle_flag_model

        get_waffle_flag_model().objects.get_or_create(name="tiac", defaults={"everyone": None, "superusers": True})


@receiver([post_save], sender=LienLibre)
def link_added(sender, instance, **kwargs):
    revision = create_manual_version(
        instance.related_object_1,
        f"Le lien '{instance.related_object_2}' a été ajouté à la fiche",
        user=getattr(instance, "_user", None),
    )
    CustomRevisionMetaData.objects.create(revision=revision, extra_data={"field": "Évènements liés"})

    revision = create_manual_version(
        instance.related_object_2,
        f"Le lien '{instance.related_object_1}' a été ajouté à la fiche",
        user=getattr(instance, "_user", None),
    )
    CustomRevisionMetaData.objects.create(revision=revision, extra_data={"field": "Évènements liés"})


@receiver([pre_delete], sender=LienLibre)
def link_deleted(sender, instance, **kwargs):
    revision = create_manual_version(
        instance.related_object_1,
        f"Le lien '{instance.related_object_2}' a été supprimé à la fiche",
        user=getattr(instance, "_user", None),
    )
    CustomRevisionMetaData.objects.create(revision=revision, extra_data={"field": "Évènements liés"})

    revision = create_manual_version(
        instance.related_object_2,
        f"Le lien '{instance.related_object_1}' a été supprimé à la fiche",
        user=getattr(instance, "_user", None),
    )
    CustomRevisionMetaData.objects.create(revision=revision, extra_data={"field": "Évènements liés"})


@receiver([post_save], sender=Message)
def message_deleted(sender, instance: Message, **kwargs):
    if instance.is_deleted is True and instance._initial_is_deleted is False:
        notify_message_deleted(instance)
        with transaction.atomic():
            with reversion.create_revision():
                reversion.set_comment(
                    f"Le message de type '{instance.get_message_type_display()}' ayant pour titre « {instance.title} » a été supprimé"
                )
                reversion.add_meta(CustomRevisionMetaData, extra_data={"field": "Fil de suivi"})
                reversion.add_to_revision(instance.content_object)


@receiver(post_save, sender=FinSuiviContact)
def fin_suivi_added(sender, instance: FinSuiviContact, created, **kwargs):
    if created:
        with transaction.atomic():
            revision = create_manual_version(
                instance.content_object,
                f"La structure {instance.contact} a déclaré la fin de suivi sur cette fiche",
                user=getattr(instance, "_user", None),
            )
            CustomRevisionMetaData.objects.create(revision=revision, extra_data={"field": "Statut"})


@receiver(pre_delete, sender=FinSuiviContact)
def fin_suivi_removed(sender, instance, **kwargs):
    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"La structure {instance.contact} a repris le suivi sur cette fiche")
            reversion.add_meta(CustomRevisionMetaData, extra_data={"field": "Statut"})
            reversion.add_to_revision(instance.content_object)

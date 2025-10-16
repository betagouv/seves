import reversion
from django.db import transaction
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from tiac.models import Etablissement


@receiver(pre_delete, sender=Etablissement)
def create_fiche_detection_version_on_etablissement_delete(sender, instance: Etablissement, **kwargs):
    evenement = instance.evenement_simple or instance.investigation_tiac

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"L'établissement '{instance.raison_sociale}' a été supprimé de la fiche")
            reversion.add_to_revision(evenement)


@receiver(post_save, sender=Etablissement)
def create_fiche_detection_version_on_etablissement_add(sender, instance: Etablissement, created, **kwargs):
    if not created:
        return
    evenement = instance.evenement_simple or instance.investigation_tiac

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"L'établissement '{instance.raison_sociale}' a été ajouté à la fiche")
            reversion.add_to_revision(evenement)

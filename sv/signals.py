from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db import transaction
import reversion

from sv.models import Lieu, Prelevement


@receiver(pre_delete, sender=Lieu)
def create_fiche_detection_version_on_lieu_delete(sender, instance: Lieu, **kwargs):
    fiche = instance.fiche_detection

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"Le lieu '{instance.nom}' a été supprimé de la fiche")
            reversion.add_to_revision(fiche)


@receiver(post_save, sender=Lieu)
def create_fiche_detection_version_on_lieu_add(sender, instance: Lieu, created, **kwargs):
    if not created:
        return
    fiche = instance.fiche_detection

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"Le lieu '{instance.nom}' a été ajouté à la fiche")
            reversion.add_to_revision(fiche)


@receiver(post_save, sender=Prelevement)
def create_fiche_detection_version_on_prelevement_add(sender, instance: Prelevement, created, **kwargs):
    if not created:
        return
    fiche = instance.lieu.fiche_detection

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(
                f"Le prélèvement pour le lieu '{instance.lieu.nom}' et la structure '{instance.structure_preleveuse}' a été ajouté à la fiche"
            )
            reversion.add_to_revision(fiche)


@receiver(pre_delete, sender=Prelevement)
def create_fiche_detection_version_on_prelevement_delete(sender, instance: Prelevement, **kwargs):
    fiche = instance.lieu.fiche_detection

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(
                f"Le prélèvement pour le lieu '{instance.lieu.nom}' et la structure '{instance.structure_preleveuse}' a été supprimé de la fiche"
            )
            reversion.add_to_revision(fiche)

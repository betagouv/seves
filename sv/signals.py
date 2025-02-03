from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db import transaction
import reversion
from django.forms.models import model_to_dict

from sv.models import Lieu, Prelevement, ZoneInfestee, FicheZoneDelimitee, VersionFicheZoneDelimitee


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


@receiver(post_save, sender=ZoneInfestee)
def create_fiche_zone_delimitee_version_on_zone_infestee_add(sender, instance: ZoneInfestee, created, **kwargs):
    if not created:
        return
    fiche = instance.fiche_zone_delimitee

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"La zone infestée '{instance.nom}' a été ajoutée à la fiche")
            reversion.add_to_revision(fiche)


@receiver(pre_delete, sender=ZoneInfestee)
def create_fiche_zone_delimitee_version_on_zone_infestee_delete(sender, instance: ZoneInfestee, **kwargs):
    fiche = instance.fiche_zone_delimitee

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"La zone infestée '{instance.nom}' a été supprimée de la fiche")
            reversion.add_to_revision(fiche)


@receiver(pre_delete, sender=FicheZoneDelimitee)
def create_evenement_version_on_fiche_zone_delimitee_delete(sender, instance: FicheZoneDelimitee, **kwargs):
    evenement = instance.evenement

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"La fiche zone délimitée '{evenement.numero}' a été supprimée.")
            zone_data = model_to_dict(instance)
            zone_data["createur"] = model_to_dict(instance.createur)
            zones_infestees = instance.zoneinfestee_set.all()
            zone_data["zones_infestees"] = [model_to_dict(zi) for zi in zones_infestees]
            reversion.add_to_revision(evenement)
            reversion.add_meta(VersionFicheZoneDelimitee, fiche_zone_delimitee_data=zone_data)

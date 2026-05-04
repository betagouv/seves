from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
import reversion

from core.diffs import force_update_on_version
from sv.models import FicheZoneDelimitee, Lieu, VersionFicheZoneDelimitee


@receiver(pre_delete, sender=FicheZoneDelimitee)
def create_evenement_version_on_fiche_zone_delimitee_delete(sender, instance: FicheZoneDelimitee, **kwargs):
    evenement = instance.evenement

    with transaction.atomic():
        with reversion.create_revision():
            reversion.set_comment(f"La fiche zone délimitée '{evenement.numero}' a été supprimée.")
            zone_data = model_to_dict(instance)
            zone_data["createur"] = model_to_dict(instance.createur)
            zones_infestees = instance.zones_infestees.all()
            zone_data["zones_infestees"] = [model_to_dict(zi) for zi in zones_infestees]
            reversion.add_to_revision(evenement)
            reversion.add_meta(VersionFicheZoneDelimitee, fiche_zone_delimitee_data=zone_data)


@receiver(pre_delete, sender=Lieu)
def create_version_on_fiche_detection_when_lieu_is_deleted_without_any_other_modification(
    sender, instance: Lieu, **kwargs
):
    force_update_on_version(instance.fiche_detection)

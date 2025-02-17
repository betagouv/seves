from functools import cached_property

import reversion
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import TextChoices
from django.urls import reverse
from reversion.models import Version, Revision

from core.models import Structure, UnitesMesure
from core.versions import get_versions_from_ids
from sv.managers import (
    FicheZoneManager,
)
from . import ZoneInfestee


@reversion.register()
class FicheZoneDelimitee(models.Model):
    class UnitesRayon(TextChoices):
        METRE = UnitesMesure.METRE
        KILOMETRE = UnitesMesure.KILOMETRE

    class UnitesSurfaceTamponTolale(TextChoices):
        METRE_CARRE = UnitesMesure.METRE_CARRE
        KILOMETRE_CARRE = UnitesMesure.KILOMETRE_CARRE
        HECTARE = UnitesMesure.HECTARE

    class Meta:
        verbose_name = "Fiche zone délimitée"
        verbose_name_plural = "Fiches zones délimitées"

    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Créateur")
    commentaire = models.TextField(verbose_name="Commentaire", blank=True)
    rayon_zone_tampon = models.FloatField(
        verbose_name="Rayon tampon réglementaire ou arbitré", null=True, blank=True, validators=[MinValueValidator(0)]
    )
    unite_rayon_zone_tampon = models.CharField(
        max_length=2,
        choices=UnitesRayon,
        default=UnitesRayon.KILOMETRE,
        verbose_name="Unité du rayon tampon réglementaire ou arbitré",
    )
    surface_tampon_totale = models.FloatField(
        verbose_name="Surface tampon totale", null=True, blank=True, validators=[MinValueValidator(0)]
    )
    unite_surface_tampon_totale = models.CharField(
        max_length=3,
        choices=UnitesSurfaceTamponTolale,
        default=UnitesSurfaceTamponTolale.METRE_CARRE,
        verbose_name="Unité de la surface tampon totale",
    )

    objects = FicheZoneManager()

    def get_absolute_url(self):
        return self.evenement.get_absolute_url()

    def get_update_url(self):
        return reverse("fiche-zone-delimitee-update", kwargs={"pk": self.pk})

    def __str__(self):
        if hasattr(self, "evenement"):
            return str(self.evenement.numero)
        return ""

    def can_user_delete(self, user):
        return self.evenement.can_user_access(user)

    def save(self, *args, **kwargs):
        with reversion.create_revision():
            super().save(*args, **kwargs)

    @cached_property
    def latest_version(self):
        zone_infestees = ZoneInfestee.objects.filter(fiche_zone_delimitee_id=self.pk).values_list("id", flat=True)
        zone_infestees_versions = get_versions_from_ids(zone_infestees, ZoneInfestee)

        instance_version = (
            Version.objects.get_for_object(self).select_related("revision__user__agent__structure").first()
        )

        versions = list(zone_infestees_versions) + [instance_version]
        versions = [v for v in versions if v]
        if not versions:
            return None
        return max(versions, key=lambda obj: obj.revision.date_created)


class VersionFicheZoneDelimitee(models.Model):
    revision = models.OneToOneField(Revision, on_delete=models.CASCADE)
    fiche_zone_delimitee_data = models.JSONField()

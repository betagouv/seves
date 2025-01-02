from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import TextChoices
from django.urls import reverse

from core.mixins import (
    WithFreeLinkIdsMixin,
)
from core.models import Structure, UnitesMesure, Visibilite
from sv.managers import (
    FicheZoneManager,
)
from sv.mixins import WithEtatMixin
from .common import NumeroFiche


class FicheZoneDelimitee(WithEtatMixin, WithFreeLinkIdsMixin, models.Model):
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
    numero = models.OneToOneField(
        NumeroFiche, on_delete=models.PROTECT, verbose_name="Numéro de fiche", null=True, blank=True
    )
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

    def save(self, *args, **kwargs):
        # TODO ici donner le numéro de l'evenement lié
        if not self.numero and self.visibilite == Visibilite.LOCAL:
            self.numero = NumeroFiche.get_next_numero()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("fiche-zone-delimitee-detail", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("fiche-zone-delimitee-update", kwargs={"pk": self.pk})

    def get_visibilite_update_url(self):
        return reverse("fiche-zone-visibilite-update", kwargs={"pk": self.pk})

    def __str__(self):
        return str(self.numero)

from functools import cached_property

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import TextChoices
from django.urls import reverse
import reversion
from reversion.models import Revision, Version

from core.models import Structure, UnitesMesure
from core.versions import get_versions_from_ids
from sv.managers import FicheZoneManager
from sv.models.models_mixins import WithDerniereMiseAJourMixin


@reversion.register()
class FicheZoneDelimitee(WithDerniereMiseAJourMixin, models.Model):
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

    def can_user_access(self, user):
        return self.evenement.can_user_access(user)

    def get_update_url(self):
        return reverse("sv:fiche-zone-delimitee-update", kwargs={"pk": self.pk})

    def __str__(self):
        if hasattr(self, "evenement"):
            return str(self.evenement.numero)
        return ""

    def can_be_deleted(self, user):
        return self.evenement._user_can_interact(user)

    def can_be_updated(self, user):
        return self.evenement._user_can_interact(user)

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


@reversion.register()
class ZoneInfestee(models.Model):
    class UnitesSurfaceInfesteeTotale(TextChoices):
        METRE_CARRE = UnitesMesure.METRE_CARRE
        KILOMETRE_CARRE = UnitesMesure.KILOMETRE_CARRE
        HECTARE = UnitesMesure.HECTARE

    class UnitesRayon(TextChoices):
        METRE = UnitesMesure.METRE
        KILOMETRE = UnitesMesure.KILOMETRE

    class CaracteristiquePrincipale(models.TextChoices):
        PLEIN_AIR_ZONE_PRODUCTION_CHAMP = (
            "plein_air_zone_production_champ",
            "(1) Plein air — zone de production (1.1) champ (culture, pâturage)",
        )
        PLEIN_AIR_ZONE_PRODUCTION_VERGER_VIGNE = (
            "plein_air_zone_production_verger_vigne",
            "(1) Plein air — zone de production (1.2) verger/vigne",
        )
        PLEIN_AIR_ZONE_PRODUCTION_PEPINIERE = (
            "plein_air_zone_production_pepiniere",
            "(1) Plein air — zone de production (1.3) pépinière",
        )
        PLEIN_AIR_ZONE_PRODUCTION_FORET = (
            "plein_air_zone_production_foret",
            "(1) Plein air — zone de production (1.4) forêt",
        )
        PLEIN_AIR_AUTRE_JARDIN_PRIVE = "plein_air_autre_jardin_prive", "(2) Plein air — autre (2.1) jardin privé"
        PLEIN_AIR_AUTRE_SITES_PUBLICS = "plein_air_autre_sites_publics", "(2) Plein air — autre (2.2) sites publics"
        PLEIN_AIR_AUTRE_ZONE_PROTEGEE = "plein_air_autre_zone_protegee", "(2) Plein air — autre (2.3) zone protégée"
        PLEIN_AIR_AUTRE_PLANTES_SAUVAGES = (
            "plein_air_autre_plantes_sauvages",
            "(2) Plein air — autre (2.4) plantes sauvages dans des zones non protégées",
        )
        PLEIN_AIR_AUTRE_AUTRE = "plein_air_autre_autre", "(2) Plein air — autre"
        ENVIRONNEMENT_FERME_SERRE = "environnement_ferme_serre", "(3) Environnement fermé (3.1) serre"
        ENVIRONNEMENT_FERME_AUTRES_JARDINS_HIVER = (
            "environnement_ferme_autres_jardins_hiver",
            "(3) Environnement fermé (3.2) autres jardins d’hiver",
        )
        ENVIRONNEMENT_FERME_SITE_PRIVE = (
            "environnement_ferme_site_prive",
            "(3) Environnement fermé (3.3) site privé (autre qu’une serre)",
        )
        ENVIRONNEMENT_FERME_SITE_PUBLIC = (
            "environnement_ferme_site_public",
            "(3) Environnement fermé (3.4) site public (autre qu’une serre)",
        )
        ENVIRONNEMENT_FERME_AUTRE = (
            "environnement_ferme_autre",
            "(3) Environnement fermé (3.5) autre",
        )

    class Meta:
        verbose_name = "Zone infestée"
        verbose_name_plural = "Zones infestées"

    fiche_zone_delimitee = models.ForeignKey("FicheZoneDelimitee", on_delete=models.CASCADE, verbose_name="Fiche zone")
    nom = models.CharField(max_length=50, verbose_name="Nom de la zone infestée", blank=True)
    surface_infestee_totale = models.FloatField(
        verbose_name="Surface infestée totale", blank=True, null=True, validators=[MinValueValidator(0)]
    )
    unite_surface_infestee_totale = models.CharField(
        max_length=3,
        choices=UnitesSurfaceInfesteeTotale,
        default=UnitesSurfaceInfesteeTotale.METRE_CARRE,
        verbose_name="Unité de la surface infestée totale",
    )
    rayon = models.FloatField(
        verbose_name="Rayon de la zone infestée", blank=True, null=True, validators=[MinValueValidator(0)]
    )
    unite_rayon = models.CharField(
        max_length=2,
        choices=UnitesRayon,
        default=UnitesRayon.KILOMETRE,
        verbose_name="Unité du rayon de la zone infestée",
    )
    caracteristique_principale = models.CharField(
        max_length=50,
        choices=CaracteristiquePrincipale.choices,
        verbose_name="Caractéristique principale",
        blank=True,
    )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                super().save(*args, **kwargs)
            FicheZoneDelimitee.objects.update_date_derniere_mise_a_jour(self.fiche_zone_delimitee.id)

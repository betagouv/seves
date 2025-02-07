import reversion
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import TextChoices, Q
from django.db.models.aggregates import Max
from django.urls import reverse
from reversion.models import Version

from core.mixins import (
    AllowsSoftDeleteMixin,
)
from core.models import Structure, UnitesMesure
from core.versions import get_versions_from_ids
from sv.managers import (
    FicheDetectionManager,
)
from .lieux import Lieu
from .prelevements import Prelevement


class Contexte(models.Model):
    class Meta:
        verbose_name = "Contexte"
        verbose_name_plural = "Contextes"

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom


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
        PLEIN_AIR_AUTRE_AUTRE = "plein_air_autre_autre", "(2) Plein air — autre (2.5) autre (veuillez préciser)"
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
            "(3) Environnement fermé (3.5) autre (veuillez préciser)",
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
        with reversion.create_revision():
            super().save(*args, **kwargs)


class StatutEvenement(models.Model):
    class Meta:
        verbose_name = "Statut de l'événement"
        verbose_name_plural = "Statuts de l'événement"
        db_table = "sv_statut_evenement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


@reversion.register()
class FicheDetection(
    AllowsSoftDeleteMixin,
    models.Model,
):
    class Meta:
        verbose_name = "Fiche détection"
        verbose_name_plural = "Fiches détection"
        db_table = "sv_fiche_detection"
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(hors_zone_infestee__isnull=True) & Q(zone_infestee__isnull=True)
                    | Q(hors_zone_infestee__isnull=True) & Q(zone_infestee__isnull=False)
                    | Q(hors_zone_infestee__isnull=False) & Q(zone_infestee__isnull=True)
                ),
                name="check_hors_zone_infestee_or_zone_infestee_or_none",
            ),
            models.UniqueConstraint(fields=["evenement", "numero_detection"], name="unique_evenement_numero_detection"),
        ]

    # Informations générales
    numero_detection = models.PositiveIntegerField(verbose_name="Numéro de détection")
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    numero_europhyt = models.CharField(max_length=8, verbose_name="Numéro Europhyt", blank=True)
    numero_rasff = models.CharField(max_length=9, verbose_name="Numéro RASFF", blank=True)
    statut_evenement = models.ForeignKey(
        StatutEvenement,
        on_delete=models.PROTECT,
        verbose_name="Statut de l'événement",
        blank=True,
        null=True,
    )
    contexte = models.ForeignKey(
        Contexte,
        on_delete=models.PROTECT,
        verbose_name="Contexte",
        blank=True,
        null=True,
    )
    date_premier_signalement = models.DateField(verbose_name="Date premier signalement", blank=True, null=True)
    commentaire = models.TextField(verbose_name="Commentaire", blank=True)

    # Mesures de gestion
    mesures_conservatoires_immediates = models.TextField(verbose_name="Mesures conservatoires immédiates", blank=True)
    mesures_consignation = models.TextField(verbose_name="Mesures de consignation", blank=True)
    mesures_phytosanitaires = models.TextField(verbose_name="Mesures phytosanitaires", blank=True)
    mesures_surveillance_specifique = models.TextField(verbose_name="Mesures de surveillance spécifique", blank=True)

    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    hors_zone_infestee = models.ForeignKey("FicheZoneDelimitee", on_delete=models.SET_NULL, null=True, blank=True)
    zone_infestee = models.ForeignKey("ZoneInfestee", on_delete=models.SET_NULL, null=True, blank=True)
    evenement = models.ForeignKey("Evenement", on_delete=models.PROTECT, null=False, related_name="detections")
    vegetaux_infestes = models.TextField(verbose_name="Nombre ou volume de végétaux infestés", blank=True)

    objects = FicheDetectionManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_state = {}
        self._original_state["hors_zone_infestee"] = self.hors_zone_infestee_id
        self._original_state["zone_infestee"] = self.zone_infestee_id

    def _save(self, *args, **kwargs):
        self._original_state["hors_zone_infestee"] = self.hors_zone_infestee_id
        self._original_state["zone_infestee"] = self.zone_infestee_id
        if not self.numero_detection:
            self.numero_detection = self.get_next_numero_detection()
        super().save(*args, **kwargs)

    @transaction.atomic
    def get_next_numero_detection(self):
        result = (
            FicheDetection.objects.select_for_update()
            .filter(evenement_id=self.evenement_id)
            .aggregate(max_numero=Max("numero_detection"))
        )
        return (result["max_numero"] or 0) + 1

    @property
    def numero(self):
        return f"{self.evenement.numero}.{self.numero_detection}"

    def _handle_hors_zone_infestee_change(self):
        if self.hors_zone_infestee_id and self._original_state["hors_zone_infestee"] is None:
            with reversion.create_revision():
                reversion.set_comment(f"La fiche détection '{self.pk}' a été ajoutée en hors zone infestée")
                reversion.add_to_revision(self.hors_zone_infestee)
        elif self._original_state["hors_zone_infestee"] and self.hors_zone_infestee_id is None:
            from . import FicheZoneDelimitee

            with reversion.create_revision():
                reversion.set_comment(f"La fiche détection '{self.pk}' a été retirée en hors zone infestée")
                reversion.add_to_revision(FicheZoneDelimitee.objects.get(pk=self._original_state["hors_zone_infestee"]))

    def _handle_zone_infestee_change(self):
        if self.zone_infestee_id and self._original_state["zone_infestee"] is None:
            with reversion.create_revision():
                reversion.set_comment(f"La fiche détection '{self.pk}' a été ajoutée en zone infestée")
                reversion.add_to_revision(self.zone_infestee)
        elif self._original_state["zone_infestee"] and self.zone_infestee_id is None:
            with reversion.create_revision():
                reversion.set_comment(f"La fiche détection '{self.pk}' a été retirée de la zone infestée")
                reversion.add_to_revision(ZoneInfestee.objects.get(pk=self._original_state["zone_infestee"]))

    def save(self, *args, **kwargs):
        need_revision = True
        if self.hors_zone_infestee_id != self._original_state["hors_zone_infestee"]:
            self._handle_hors_zone_infestee_change()
            self._save(*args, **kwargs)
            need_revision = False
        if self.zone_infestee_id != self._original_state["zone_infestee"]:
            self._handle_zone_infestee_change()
            self._save(*args, **kwargs)
            need_revision = False

        if need_revision:
            with reversion.create_revision():
                self._save(*args, **kwargs)

    def get_absolute_url(self):
        return self.evenement.get_absolute_url()

    def get_update_url(self):
        return reverse("fiche-detection-modification", kwargs={"pk": self.pk})

    def can_user_delete(self, user):
        return self.evenement.can_user_access(user)

    def __str__(self):
        return self.numero

    @property
    def is_linked_to_fiche_zone_delimitee(self):
        return self.hors_zone_infestee is not None or self.zone_infestee is not None

    def get_fiche_zone_delimitee(self):
        if self.hors_zone_infestee:
            return self.hors_zone_infestee
        if self.zone_infestee and self.zone_infestee.fiche_zone_delimitee:
            return self.zone_infestee.fiche_zone_delimitee

    @property
    def latest_version(self):
        lieux_ids = list(self.lieux.all().values_list("id", flat=True))
        lieu_versions = get_versions_from_ids(lieux_ids, Lieu)

        prelevements = Prelevement.objects.filter(lieu__fiche_detection__pk=self.pk).values_list("id", flat=True)
        prelevement_versions = get_versions_from_ids(prelevements, Prelevement)

        instance_version = Version.objects.get_for_object(self).select_related("revision").first()

        versions = list(lieu_versions) + list(prelevement_versions) + [instance_version]
        versions = [v for v in versions if v]
        if not versions:
            return None
        return max(versions, key=lambda obj: obj.revision.date_created)

import reversion
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import TextChoices, Q
from django.urls import reverse
from reversion.models import Version

from core.mixins import (
    AllowsSoftDeleteMixin,
    AllowACNotificationMixin,
    AllowVisibiliteMixin,
    WithMessageUrlsMixin,
    WithFreeLinkIdsMixin,
)
from core.models import Document, Message, Contact, Structure, FinSuiviContact, UnitesMesure, Visibilite
from sv.managers import (
    FicheDetectionManager,
)
from sv.mixins import WithEtatMixin
from .common import NumeroFiche, OrganismeNuisible, StatutReglementaire, Etat
from .prelevements import Prelevement
from .lieux import Lieu


class Contexte(models.Model):
    class Meta:
        verbose_name = "Contexte"
        verbose_name_plural = "Contextes"

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom


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
    AllowACNotificationMixin,
    AllowVisibiliteMixin,
    WithEtatMixin,
    WithMessageUrlsMixin,
    WithFreeLinkIdsMixin,
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
            models.CheckConstraint(
                check=~(Q(visibilite="brouillon") & Q(numero__isnull=False)),
                name="check_numero_fiche_is_null_when_visibilite_is_brouillon",
            ),
        ]

    # Informations générales
    numero = models.OneToOneField(
        NumeroFiche, on_delete=models.PROTECT, verbose_name="Numéro de fiche", null=True, blank=True
    )
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

    # Objet de l'événement
    organisme_nuisible = models.ForeignKey(
        OrganismeNuisible,
        on_delete=models.PROTECT,
        verbose_name="OEPP",
        blank=True,
        null=True,
    )
    statut_reglementaire = models.ForeignKey(
        StatutReglementaire,
        on_delete=models.PROTECT,
        verbose_name="Statut règlementaire de l'organisme",
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

    etat = models.ForeignKey(
        Etat, on_delete=models.PROTECT, verbose_name="État de la fiche", default=Etat.get_etat_initial
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    documents = GenericRelation(Document)
    messages = GenericRelation(Message)
    contacts = models.ManyToManyField(Contact, verbose_name="Contacts", blank=True)
    fin_suivi = GenericRelation(FinSuiviContact)
    hors_zone_infestee = models.ForeignKey("FicheZoneDelimitee", on_delete=models.SET_NULL, null=True, blank=True)
    zone_infestee = models.ForeignKey("ZoneInfestee", on_delete=models.SET_NULL, null=True, blank=True)
    vegetaux_infestes = models.TextField(verbose_name="Nombre ou volume de végétaux infestés", blank=True)

    objects = FicheDetectionManager()

    def save(self, *args, **kwargs):
        with reversion.create_revision():
            if not self.numero and self.visibilite == Visibilite.LOCAL:
                self.numero = NumeroFiche.get_next_numero()
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("fiche-detection-vue-detaillee", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("fiche-detection-modification", kwargs={"pk": self.pk})

    def get_visibilite_update_url(self):
        return reverse("fiche-detection-visibilite-update", kwargs={"pk": self.pk})

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def __str__(self):
        return str(self.numero)

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
        content_type = ContentType.objects.get_for_model(Lieu)
        lieu_versions = Version.objects.select_related("revision").filter(
            content_type=content_type, object_id__in=lieux_ids
        )

        prelevements = Prelevement.objects.filter(lieu__fiche_detection__pk=self.pk).values_list("id", flat=True)
        content_type = ContentType.objects.get_for_model(Prelevement)
        prelevement_versions = Version.objects.select_related("revision").filter(
            content_type=content_type, object_id__in=list(prelevements)
        )

        instance_version = Version.objects.get_for_object(self).select_related("revision").first()

        versions = list(lieu_versions) + list(prelevement_versions) + [instance_version]
        versions = [v for v in versions if v]
        if not versions:
            return None
        return max(versions, key=lambda obj: obj.revision.date_created)

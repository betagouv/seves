import re

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.core.validators import RegexValidator, MinValueValidator
from django.db.models import TextChoices, Q
from django.contrib.contenttypes.fields import GenericRelation
import datetime

from django.urls import reverse

from core.mixins import (
    AllowsSoftDeleteMixin,
    AllowACNotificationMixin,
    AllowVisibiliteMixin,
    IsActiveMixin,
    WithMessageUrlsMixin,
    WithFreeLinkIdsMixin,
)
from core.models import Document, Message, Contact, Structure, FinSuiviContact, UnitesMesure, Visibilite
from sv.constants import STRUCTURE_EXPLOITANT
from sv.managers import (
    LaboratoireAgreeManager,
    LaboratoireConfirmationOfficielleManager,
    FicheDetectionManager,
    FicheZoneManager,
    StructurePreleveuseManager,
)
from sv.mixins import WithEtatMixin


class NumeroFiche(models.Model):
    class Meta:
        unique_together = ("annee", "numero")
        verbose_name = "Numéro de fiche"
        verbose_name_plural = "Numéros de fiche"
        db_table = "sv_numero_fiche"

    annee = models.IntegerField(verbose_name="Année")
    numero = models.IntegerField(verbose_name="Numéro")

    def __str__(self):
        return f"{self.annee}.{self.numero}"

    def _save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @classmethod
    @transaction.atomic  # Assure que la méthode est exécutée dans une transaction pour éviter les race conditions
    def get_next_numero(cls):
        annee_courante = datetime.datetime.now().year
        last_fiche = cls.objects.filter(annee=annee_courante).order_by("-numero").first()

        # Si une fiche existe déjà pour cette année
        # On incrémente le numéro
        # Si aucune fiche n'existe pour cette année
        # On réinitialise le numéro à 1
        if last_fiche is not None:
            numero = last_fiche.numero + 1
        else:
            numero = 1

        new_fiche = cls(annee=annee_courante, numero=numero)
        new_fiche._save()
        return new_fiche


class OrganismeNuisible(models.Model):
    class Meta:
        verbose_name = "Organisme nuisible"
        verbose_name_plural = "Organismes nuisibles"
        db_table = "sv_organisme_nuisible"
        constraints = [
            models.UniqueConstraint(
                fields=["code_oepp", "libelle_court"], name="unique_organisme_nuisible_code_libelle"
            )
        ]

    code_oepp = models.CharField(verbose_name="Code OEPP", unique=True)
    libelle_court = models.CharField(max_length=255, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.libelle_court


class StatutReglementaire(models.Model):
    class Meta:
        verbose_name = "Statut règlementaire de l'organisme"
        verbose_name_plural = "Statuts règlementaires de l'organisme"
        db_table = "sv_statut_reglementaire"
        constraints = [
            models.UniqueConstraint(fields=["code", "libelle"], name="unique_statut_reglementaire_code_libelle")
        ]

    code = models.CharField(max_length=10, verbose_name="Code", unique=True)
    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class Contexte(models.Model):
    class Meta:
        verbose_name = "Contexte"
        verbose_name_plural = "Contextes"

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom


class Region(models.Model):
    class Meta:
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom


class Departement(models.Model):
    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ["numero"]
        constraints = [models.UniqueConstraint(fields=["numero", "nom"], name="unique_departement_numero_nom")]

    numero = models.CharField(max_length=3, verbose_name="Numéro", unique=True)
    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, verbose_name="Région")

    def __str__(self):
        return f"{self.numero} - {self.nom}"


def validate_wgs84_longitude(value):
    if value is not None and (value < -180 or value > 180):
        raise ValidationError("La longitude doit être comprise entre -180° et +180°")


def validate_wgs84_latitude(value):
    if value is not None and (value < -90 or value > 90):
        raise ValidationError("La latitude doit être comprise entre -90° et +90°")


class Lieu(models.Model):
    class Meta:
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"

    fiche_detection = models.ForeignKey(
        "FicheDetection",
        on_delete=models.CASCADE,
        verbose_name="Fiche de détection",
        related_name="lieux",
    )
    nom = models.CharField(max_length=100, verbose_name="Nom")
    wgs84_longitude = models.FloatField(
        verbose_name="Longitude WGS84", blank=True, null=True, validators=[validate_wgs84_longitude]
    )
    wgs84_latitude = models.FloatField(
        verbose_name="Latitude WGS84", blank=True, null=True, validators=[validate_wgs84_latitude]
    )
    adresse_lieu_dit = models.CharField(max_length=100, verbose_name="Adresse ou lieu-dit", blank=True)
    commune = models.CharField(max_length=100, verbose_name="Commune", blank=True)
    code_insee = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Code INSEE de la commune",
        validators=[
            RegexValidator(
                regex="^[0-9]{5}$",
                message="Le code INSEE doit contenir exactement 5 chiffres",
                code="invalid_code_insee",
            ),
        ],
    )
    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        verbose_name="Département",
        blank=True,
        null=True,
    )
    is_etablissement = models.BooleanField(verbose_name="Établissement", default=False)
    nom_etablissement = models.CharField(max_length=100, verbose_name="Nom établissement", blank=True)
    activite_etablissement = models.CharField(max_length=100, verbose_name="Activité établissement", blank=True)
    pays_etablissement = models.CharField(max_length=100, verbose_name="Pays établissement", blank=True)
    raison_sociale_etablissement = models.CharField(
        max_length=100, verbose_name="Raison sociale établissement", blank=True
    )
    adresse_etablissement = models.CharField(max_length=100, verbose_name="Adresse établissement", blank=True)
    siret_etablissement = models.CharField(max_length=100, verbose_name="SIRET établissement", blank=True)
    site_inspection = models.ForeignKey(
        "SiteInspection",
        on_delete=models.PROTECT,
        verbose_name="Site d'inspection",
        blank=True,
        null=True,
    )
    position_chaine_distribution_etablissement = models.ForeignKey(
        "PositionChaineDistribution",
        on_delete=models.PROTECT,
        verbose_name="Position dans la chaîne de distribution établissement",
        blank=True,
        null=True,
    )
    code_inupp_etablissement = models.CharField(max_length=50, verbose_name="Code INUPP", blank=True)

    ETABLISSEMENT_FIELDS = [
        "nom_etablissement",
        "activite_etablissement",
        "pays_etablissement",
        "raison_sociale_etablissement",
        "adresse_etablissement",
        "siret_etablissement",
        "site_inspection",
        "position_chaine_distribution_etablissement",
        "code_inupp_etablissement",
    ]

    def __str__(self):
        return str(self.nom)


class StatutEtablissement(models.Model):
    class Meta:
        verbose_name = "Statut de l'établissement"
        verbose_name_plural = "Statuts de l'établissement"
        db_table = "sv_statut_etablissement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class PositionChaineDistribution(models.Model):
    class Meta:
        verbose_name = "Position dans la chaîne de distribution"
        verbose_name_plural = "Positions dans la chaîne de distribution"
        db_table = "sv_position_chaine_distribution"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class StructurePreleveuse(IsActiveMixin, models.Model):
    class Meta:
        verbose_name = "Structure préleveuse"
        verbose_name_plural = "Structures préleveuses"
        db_table = "sv_structure_preleveur"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    objects = StructurePreleveuseManager()

    def __str__(self):
        return self.nom


class SiteInspection(models.Model):
    class Meta:
        verbose_name = "Site d'inspection"
        verbose_name_plural = "Sites d'inspection"
        db_table = "sv_site_inspection"

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom


class MatricePrelevee(models.Model):
    class Meta:
        verbose_name = "Matrice prélevée"
        verbose_name_plural = "Matrices prélevées"
        db_table = "sv_matrice_prelevee"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class EspeceEchantillon(models.Model):
    class Meta:
        verbose_name = "Espèce de l'échantillon"
        verbose_name_plural = "Espèces de l'échantillon"
        db_table = "sv_espece_echantillon"
        constraints = [
            models.UniqueConstraint(fields=["code_oepp", "libelle"], name="unique_espece_echantillon_codeoepp_libelle")
        ]

    code_oepp = models.CharField(max_length=100, verbose_name="Code OEPP", unique=True)
    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class LaboratoireAgree(IsActiveMixin, models.Model):
    class Meta:
        verbose_name = "Laboratoire agréé"
        verbose_name_plural = "Laboratoires agréés"
        db_table = "sv_laboratoire_agree"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom

    objects = LaboratoireAgreeManager()


class LaboratoireConfirmationOfficielle(IsActiveMixin, models.Model):
    class Meta:
        verbose_name = "Laboratoire de confirmation officielle"
        verbose_name_plural = "Laboratoires de confirmation officielle"
        db_table = "sv_laboratoire_confirmation_officielle"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom

    objects = LaboratoireConfirmationOfficielleManager()


def validate_numero_rapport_inspection(value):
    pattern = r"^\d{2}-\d{6}$"
    if not re.match(pattern, value):
        raise ValidationError(
            "Le format doit être AA-XXXXXX où AA correspond à l'année sur 2 chiffres (ex: 24 pour 2024) et XXXXXX est un numéro à 6 chiffres"
        )


class Prelevement(models.Model):
    class Resultat(models.TextChoices):
        DETECTE = "detecte", "Détecté"
        NON_DETECTE = "non_detecte", "Non détecté"

    class Meta:
        verbose_name = "Prélèvement"
        verbose_name_plural = "Prélèvements"
        db_table = "sv_prelevement"
        constraints = [
            models.CheckConstraint(
                check=Q(is_officiel=True)
                | (
                    Q(laboratoire_agree__isnull=True)
                    & Q(laboratoire_confirmation_officielle__isnull=True)
                    & Q(numero_rapport_inspection="")
                ),
                name="check_officiel_fields_empty_or_null",
            )
        ]

    lieu = models.ForeignKey(Lieu, on_delete=models.CASCADE, verbose_name="Lieu", related_name="prelevements")
    structure_preleveuse = models.ForeignKey(
        StructurePreleveuse, on_delete=models.PROTECT, verbose_name="Structure préleveuse"
    )
    numero_echantillon = models.CharField(max_length=100, verbose_name="Numéro d'échantillon", blank=True)
    date_prelevement = models.DateField(verbose_name="Date de prélèvement", blank=True, null=True)
    matrice_prelevee = models.ForeignKey(
        MatricePrelevee,
        on_delete=models.PROTECT,
        verbose_name="Matrice prélevée",
        blank=True,
        null=True,
    )
    espece_echantillon = models.ForeignKey(
        EspeceEchantillon,
        on_delete=models.PROTECT,
        verbose_name="Espèce de l'échantillon",
        blank=True,
        null=True,
    )
    is_officiel = models.BooleanField(verbose_name="Prélèvement officiel", default=False)
    laboratoire_agree = models.ForeignKey(
        "LaboratoireAgree",
        on_delete=models.PROTECT,
        verbose_name="Laboratoire agréé",
        blank=True,
        null=True,
    )
    laboratoire_confirmation_officielle = models.ForeignKey(
        "LaboratoireConfirmationOfficielle",
        on_delete=models.PROTECT,
        verbose_name="Laboratoire de confirmation officielle",
        blank=True,
        null=True,
    )
    resultat = models.CharField(max_length=50, choices=Resultat.choices, verbose_name="Résultat")
    numero_rapport_inspection = models.CharField(
        max_length=9,
        verbose_name="Numéro du rapport d'inspection",
        blank=True,
        validators=[validate_numero_rapport_inspection],
    )

    OFFICIEL_FIELDS = ["numero_rapport_inspection", "laboratoire_agree", "laboratoire_confirmation_officielle"]

    def __str__(self):
        return f"Prélèvement n° {self.id}"

    @property
    def is_result_positive(self):
        return self.resultat in Prelevement.Resultat.DETECTE

    def clean(self):
        super().clean()
        if self.is_officiel and self.structure_preleveuse.nom == STRUCTURE_EXPLOITANT:
            raise ValidationError("Le prélèvement ne peut pas être officiel pour une structure 'Exploitant'")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class StatutEvenement(models.Model):
    class Meta:
        verbose_name = "Statut de l'événement"
        verbose_name_plural = "Statuts de l'événement"
        db_table = "sv_statut_evenement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class Etat(models.Model):
    NOUVEAU = "nouveau"
    EN_COURS = "en cours"
    CLOTURE = "clôturé"

    class Meta:
        verbose_name = "Etat"
        verbose_name_plural = "Etats"
        db_table = "sv_etat"

    libelle = models.CharField(max_length=30, unique=True)

    @classmethod
    def get_etat_initial(cls):
        return cls.objects.get(libelle=cls.NOUVEAU).id

    @classmethod
    def get_etat_cloture(cls):
        return cls.objects.get(libelle=cls.CLOTURE)

    def is_cloture(self):
        return self.libelle == self.CLOTURE

    def __str__(self):
        return self.libelle


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
        if not self.numero and self.visibilite == Visibilite.LOCAL:
            self.numero = NumeroFiche.get_next_numero()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("fiche-detection-vue-detaillee", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("fiche-detection-modification", kwargs={"pk": self.pk})

    def get_visibilite_update_url(self):
        return reverse("fiche-detection-visibilite-update", kwargs={"pk": self.pk})

    def __str__(self):
        return str(self.numero)

    @property
    def is_linked_to_fiche_zone_delimitee(self):
        return self.hors_zone_infestee is not None or self.zone_infestee is not None

    def get_fiche_zone_delimitee(self) -> "FicheZoneDelimitee | None":
        if self.hors_zone_infestee:
            return self.hors_zone_infestee
        if self.zone_infestee and self.zone_infestee.fiche_zone_delimitee:
            return self.zone_infestee.fiche_zone_delimitee


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


class FicheZoneDelimitee(AllowVisibiliteMixin, WithEtatMixin, WithMessageUrlsMixin, WithFreeLinkIdsMixin, models.Model):
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
        constraints = [
            models.CheckConstraint(
                check=~(Q(visibilite="brouillon") & Q(numero__isnull=False)),
                name="check_fiche_zone_delimitee_numero_fiche_is_null_when_visibilite_is_brouillon",
            ),
        ]

    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    numero = models.OneToOneField(
        NumeroFiche, on_delete=models.PROTECT, verbose_name="Numéro de fiche", null=True, blank=True
    )
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Créateur")
    organisme_nuisible = models.ForeignKey(
        OrganismeNuisible,
        on_delete=models.PROTECT,
        verbose_name="Organisme nuisible",
    )
    statut_reglementaire = models.ForeignKey(
        StatutReglementaire,
        on_delete=models.PROTECT,
        verbose_name="Statut règlementaire de l'organisme nuisible",
    )
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
    etat = models.ForeignKey(
        Etat, on_delete=models.PROTECT, verbose_name="État de la fiche", default=Etat.get_etat_initial
    )

    documents = GenericRelation(Document)
    messages = GenericRelation(Message)
    contacts = models.ManyToManyField(Contact, verbose_name="Contacts", blank=True)
    fin_suivi = GenericRelation(FinSuiviContact)

    objects = FicheZoneManager()

    def save(self, *args, **kwargs):
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

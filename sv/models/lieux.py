import reversion
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction
from django_countries.fields import CountryField


class PositionChaineDistribution(models.Model):
    class Meta:
        verbose_name = "Position dans la chaîne de distribution"
        verbose_name_plural = "Positions dans la chaîne de distribution"
        db_table = "sv_position_chaine_distribution"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


class Region(models.Model):
    class Meta:
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

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


@reversion.register()
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
    activite_etablissement = models.CharField(max_length=100, verbose_name="Activité établissement", blank=True)
    pays_etablissement = CountryField(verbose_name="Pays établissement", blank=True)
    raison_sociale_etablissement = models.CharField(
        max_length=100, verbose_name="Raison sociale établissement", blank=True
    )
    adresse_etablissement = models.CharField(max_length=100, verbose_name="Adresse établissement", blank=True)
    siret_etablissement = models.CharField(
        max_length=14,
        verbose_name="SIRET établissement",
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{14}$",
                message="Le SIRET doit contenir exactement 14 chiffres",
                code="invalid_siret",
            ),
        ],
    )
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
    code_inupp_etablissement = models.CharField(max_length=10, verbose_name="Code INUPP", blank=True)

    ETABLISSEMENT_FIELDS = [
        "activite_etablissement",
        "pays_etablissement",
        "raison_sociale_etablissement",
        "adresse_etablissement",
        "siret_etablissement",
        "code_inupp_etablissement",
        "position_chaine_distribution_etablissement",
    ]

    def __str__(self):
        return str(self.nom)

    def save(self, *args, **kwargs):
        from sv.models import FicheDetection

        with transaction.atomic():
            with reversion.create_revision():
                super().save(*args, **kwargs)
            FicheDetection.objects.update_date_derniere_mise_a_jour(self.fiche_detection.id)

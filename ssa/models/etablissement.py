import reversion
from django.core.validators import RegexValidator

from django.db import models
from django_countries.fields import CountryField

from core.models import Departement
from ssa.models import EvenementProduit
from ssa.models.validators import validate_numero_agrement


class PositionDossier(models.TextChoices):
    DETECTION_NON_CONFORMITE = "detection_non_conformite", "Détection de la non-conformité"
    SURVENUE_NON_CONFORMITE = "survenue_non_conformite", "Survenue de la non-conformité"
    DETECTION_ET_SURVENUE_NON_CONFORMITE = (
        "detection_et_survenue_non_conformite",
        "Détection et survenue de la non-conformité",
    )
    AUTRE_MAILLON_CHAINE_DISTRIBUTION = (
        "autre_maillon_chaine_distribution",
        "Autre maillon de la chaîne de distribution",
    )
    AUTRE = "autre", "Autre"


@reversion.register()
class Etablissement(models.Model):
    evenement_produit = models.ForeignKey(EvenementProduit, on_delete=models.PROTECT, related_name="etablissements")

    siret = models.CharField(
        max_length=14,
        verbose_name="SIRET de l'établissement",
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{14}$",
                message="Le SIRET doit contenir exactement 14 chiffres",
                code="invalid_siret",
            ),
        ],
    )
    numero_agrement = models.CharField(
        max_length=12, verbose_name="Numéro d'agrément", blank=True, validators=[validate_numero_agrement]
    )
    raison_sociale = models.CharField(max_length=100, verbose_name="Raison sociale")

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
        related_name="etablissements",
        blank=True,
        null=True,
    )
    pays = CountryField(null=True)

    type_exploitant = models.CharField(max_length=45, verbose_name="Type exploitant", blank=True)
    position_dossier = models.CharField(
        max_length=100, choices=PositionDossier.choices, verbose_name="Position dossier", blank=True
    )
    numeros_resytal = models.CharField(max_length=255, verbose_name="Numéros d’inspection Resytal", blank=True)

    def __str__(self):
        return f"{self.raison_sociale}"

    def save(self, *args, **kwargs):
        with reversion.create_revision():
            super().save(*args, **kwargs)

    @classmethod
    def get_position_dossier_css_class(self, value):
        IMPORTANT_CASES = [
            PositionDossier.SURVENUE_NON_CONFORMITE,
            PositionDossier.DETECTION_NON_CONFORMITE,
            PositionDossier.DETECTION_ET_SURVENUE_NON_CONFORMITE,
        ]
        return "fr-badge--info" if value in IMPORTANT_CASES else ""

    @property
    def position_dossier_css_class(self):
        return Etablissement.get_position_dossier_css_class(self.position_dossier)

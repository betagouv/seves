import reversion
from django.db import models

from core.models import BaseEtablissement
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
class Etablissement(BaseEtablissement, models.Model):
    evenement_produit = models.ForeignKey(
        "ssa.EvenementProduit", on_delete=models.PROTECT, related_name="etablissements", null=True, default=None
    )

    investigation_cas_humain = models.ForeignKey(
        "ssa.EvenementInvestigationCasHumain",
        on_delete=models.PROTECT,
        related_name="etablissements",
        null=True,
        default=None,
    )

    numero_agrement = models.CharField(
        max_length=12, verbose_name="Numéro d'agrément", blank=True, validators=[validate_numero_agrement]
    )

    type_exploitant = models.CharField(max_length=45, verbose_name="Type exploitant", blank=True)
    position_dossier = models.CharField(
        max_length=100, choices=PositionDossier.choices, verbose_name="Position dossier", blank=True
    )
    numeros_resytal = models.CharField(max_length=255, verbose_name="Numéros d’inspection Resytal", blank=True)

    historical_data = models.JSONField(default=dict, blank=True)

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
        return self.get_position_dossier_css_class(self.position_dossier)

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(evenement_produit__isnull=False, investigation_cas_humain__isnull=True)
                    | models.Q(evenement_produit__isnull=True, investigation_cas_humain__isnull=False)
                ),
                name="either_evenement_produit_or_investigation_cas_humain",
            ),
        )

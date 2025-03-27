import re

import reversion
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from core.mixins import IsActiveMixin
from sv.constants import STRUCTURE_EXPLOITANT
from sv.managers import (
    StructurePreleveuseManager,
    LaboratoireManager,
)
from .lieux import Lieu


class MatricePrelevee(models.Model):
    class Meta:
        verbose_name = "Matrice prélevée"
        verbose_name_plural = "Matrices prélevées"
        db_table = "sv_matrice_prelevee"

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


class Laboratoire(IsActiveMixin, models.Model):
    class Meta:
        verbose_name = "Laboratoire"
        verbose_name_plural = "Laboratoires"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)
    confirmation_officielle = models.BooleanField(
        default=False, verbose_name="Peut fournir une confirmation officielle"
    )

    def __str__(self):
        return self.nom

    objects = LaboratoireManager()


def validate_numero_rapport_inspection(value):
    pattern = r"^\d{2}-\d{6}$"
    if not re.match(pattern, value):
        raise ValidationError(
            "Le format doit être AA-XXXXXX où AA correspond à l'année sur 2 chiffres (ex: 24 pour 2024) et XXXXXX est un numéro à 6 chiffres"
        )


@reversion.register()
class Prelevement(models.Model):
    class Resultat(models.TextChoices):
        DETECTE = "detecte", "Détecté"
        NON_DETECTE = "non_detecte", "Non détecté"
        NON_CONCLUSIF = "non_conclusif", "Non conclusif"

    class TypeAnalyse(models.TextChoices):
        PREMIERE_INTENTION = "premiere_intention", "1ère intention"
        CONFIRMATION = "confirmation", "Confirmation"

    class Meta:
        verbose_name = "Prélèvement"
        verbose_name_plural = "Prélèvements"
        db_table = "sv_prelevement"
        constraints = [
            models.CheckConstraint(
                condition=Q(is_officiel=True) | Q(numero_rapport_inspection=""),
                name="check_numero_officiel_empty_or_null",
            )
        ]

    lieu = models.ForeignKey(Lieu, on_delete=models.CASCADE, verbose_name="Lieu", related_name="prelevements")
    structure_preleveuse = models.ForeignKey(
        StructurePreleveuse, on_delete=models.PROTECT, verbose_name="Structure préleveuse"
    )
    numero_echantillon = models.CharField(max_length=100, verbose_name="N° d'échantillon", blank=True)
    date_prelevement = models.DateField(verbose_name="Date de prélèvement", blank=True, null=True)
    matrice_prelevee = models.ForeignKey(
        MatricePrelevee,
        on_delete=models.PROTECT,
        verbose_name="Nature de l'objet",
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
    laboratoire = models.ForeignKey(
        "Laboratoire",
        on_delete=models.PROTECT,
        verbose_name="Laboratoire",
        blank=True,
        null=True,
    )
    resultat = models.CharField(max_length=50, choices=Resultat.choices, verbose_name="Résultat")
    type_analyse = models.CharField(
        max_length=50,
        choices=TypeAnalyse.choices,
        verbose_name="Type d'analyse",
        default=TypeAnalyse.PREMIERE_INTENTION,
    )
    numero_rapport_inspection = models.CharField(
        max_length=9,
        verbose_name="Numéro du rapport d'inspection",
        blank=True,
        validators=[validate_numero_rapport_inspection],
    )

    OFFICIEL_FIELDS = ["numero_rapport_inspection", "laboratoire"]

    def __str__(self):
        return f"Prélèvement n° {self.id}"

    def clean(self):
        super().clean()
        if self.is_officiel and self.structure_preleveuse.nom == STRUCTURE_EXPLOITANT:
            raise ValidationError("Le prélèvement ne peut pas être officiel pour une structure 'Exploitant'")

        if (
            self.type_analyse == self.TypeAnalyse.CONFIRMATION
            and self.laboratoire
            and self.laboratoire.confirmation_officielle is False
        ):
            raise ValidationError(
                "Un prélèvement de confirmation ne peut être réalisé que par un laboratoire de confirmation officielle"
            )

    def save(self, *args, **kwargs):
        self.clean()
        with reversion.create_revision():
            super().save(*args, **kwargs)

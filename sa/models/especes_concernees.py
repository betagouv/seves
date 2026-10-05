from django.core.exceptions import ValidationError
from django.db import models

from sa.models.evenement import Espece


class EspeceConcernee(models.Model):
    evenement = models.ForeignKey(
        "sa.EvenementAnimal", on_delete=models.CASCADE, verbose_name="Événement", related_name="especes_exposees"
    )
    espece = models.ForeignKey(Espece, on_delete=models.PROTECT, null=False)

    identifiant = models.CharField(max_length=255, verbose_name="Identifiant", blank=True, null=True)

    presents = models.PositiveIntegerField(verbose_name="Présents", blank=True, null=True)
    morts = models.PositiveIntegerField(verbose_name="Morts", blank=True, null=True)
    cas = models.PositiveIntegerField(verbose_name="Cas", blank=True, null=True)
    abattus = models.PositiveIntegerField(verbose_name="Abattus", blank=True, null=True)
    depeuples = models.PositiveIntegerField(verbose_name="Dépeuplés/Euthanasiés", blank=True, null=True)
    vaccines = models.PositiveIntegerField(verbose_name="Vaccinés", blank=True, null=True)

    situation_unite_regle = models.ForeignKey(
        "sa.SituationUniteRegle",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="especes_concernees",
        verbose_name="Situation de l'unité",
    )

    def __str__(self):
        return f"{self.espece} pour l'événement {self.evenement}"

    @property
    def type_lieu(self):
        return self.situation_unite_regle.type_lieu if self.situation_unite_regle_id else ""

    @property
    def mode_elevage(self):
        return self.situation_unite_regle.mode_elevage if self.situation_unite_regle_id else ""

    @property
    def type_production(self):
        return self.situation_unite_regle.type_production if self.situation_unite_regle_id else ""

    @property
    def type_elevage(self):
        return self.situation_unite_regle.type_elevage if self.situation_unite_regle_id else ""

    def get_situation_unite_lines(self):
        return [
            value for value in (self.type_lieu, self.mode_elevage, self.type_production, self.type_elevage) if value
        ]

    def clean(self):
        super().clean()
        if self.situation_unite_regle_id and self.espece_id:
            if self.situation_unite_regle.espece_id != self.espece_id:
                raise ValidationError(
                    {
                        "situation_unite_regle": "La situation renseignée ne correspond pas à l'espèce sélectionnée.",
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

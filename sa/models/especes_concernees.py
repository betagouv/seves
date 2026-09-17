from django.core.exceptions import ValidationError
from django.db import models

from sa.models.evenement import Espece
from sa.referentiels import situation_unite


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

    type_lieu = models.CharField(max_length=255, verbose_name="Type de lieu", blank=True)
    mode_elevage = models.CharField(max_length=255, verbose_name="Mode d'élevage", blank=True)
    type_production = models.CharField(max_length=255, verbose_name="Type de production", blank=True)
    type_elevage = models.CharField(max_length=255, verbose_name="Type d'élevage", blank=True)

    def __str__(self):
        return f"{self.espece} pour l'événement {self.evenement}"

    def get_situation_unite_lines(self):
        return [
            value for value in (self.type_lieu, self.mode_elevage, self.type_production, self.type_elevage) if value
        ]

    def clean(self):
        super().clean()
        if self.espece_id is None:
            return
        if any((self.type_lieu, self.mode_elevage, self.type_production, self.type_elevage)):
            if not situation_unite.is_valid_combination(
                self.espece.name, self.type_lieu, self.mode_elevage, self.type_production, self.type_elevage
            ):
                raise ValidationError(
                    {
                        "type_lieu": "La situation renseignée ne correspond pas aux valeurs possibles pour cette espèce.",
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

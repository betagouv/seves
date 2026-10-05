from django.db import models

from sa.models.evenement import Espece


class SituationUniteRegle(models.Model):
    espece = models.ForeignKey(Espece, on_delete=models.CASCADE, related_name="situation_unite_regles")
    type_lieu = models.CharField(max_length=255, verbose_name="Type de lieu")
    mode_elevage = models.CharField(max_length=255, verbose_name="Mode d'élevage", blank=True)
    type_production = models.CharField(max_length=255, verbose_name="Type de production", blank=True)
    type_elevage = models.CharField(max_length=255, verbose_name="Type d'élevage", blank=True)

    class Meta:
        verbose_name = "Règle de situation de l'unité"
        verbose_name_plural = "Règles de situation de l'unité"
        constraints = [
            models.UniqueConstraint(
                fields=["espece", "type_lieu", "mode_elevage", "type_production", "type_elevage"],
                name="unique_situation_unite_regle",
            )
        ]

    def __str__(self):
        return f"{self.espece} - {self.type_lieu}"

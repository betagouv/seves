from django.db import models

from .laboratoire import Laboratoire


class MethodeAnalyse(models.Model):
    libelle = models.CharField(max_length=255, verbose_name="Libellé(s) source(s)")
    laboratoires = models.ManyToManyField(
        Laboratoire,
        verbose_name="Laboratoires",
        related_name="methodes_analyse",
        blank=True,
    )

    class Meta:
        verbose_name = "Méthode d'analyse"
        verbose_name_plural = "Méthodes d'analyse"
        ordering = ["libelle"]

    def __str__(self):
        return self.libelle

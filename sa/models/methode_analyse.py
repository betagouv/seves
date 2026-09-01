from django.db import models

from .laboratoire import Laboratoire


class MethodeAnalyse(models.Model):
    libelle_source = models.CharField(max_length=255, verbose_name="Libellé(s) source(s)")
    date_maj_source = models.DateField(verbose_name="Date de mise à jour de la source")
    laboratoires = models.ManyToManyField(
        Laboratoire,
        verbose_name="Laboratoires",
        related_name="methodes_analyse",
        blank=True,
    )

    class Meta:
        verbose_name = "Méthode d'analyse"
        verbose_name_plural = "Méthodes d'analyse"
        ordering = ["libelle_source"]

    def __str__(self):
        return self.libelle_source

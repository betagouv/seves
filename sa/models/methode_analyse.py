from django.db import models

from .laboratoire import Laboratoire


class MethodeAnalyse(models.Model):
    id_seves = models.CharField(max_length=255, unique=True, verbose_name="Identifiant Sèves")
    libelle_source = models.TextField(verbose_name="Libellé(s) source(s)")
    libelle_affichage = models.CharField(max_length=255, unique=True, verbose_name="Libellé affiché")
    actif = models.BooleanField(default=True, verbose_name="Actif")
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
        ordering = ["libelle_affichage"]

    def __str__(self):
        return self.libelle_affichage

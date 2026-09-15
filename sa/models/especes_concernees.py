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

    def __str__(self):
        return f"{self.espece} pour l'événement {self.evenement}"

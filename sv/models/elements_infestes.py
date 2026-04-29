from django.db import models

from sv.constants import ElementInfesteQuantiteUnite, ElementInfesteType
from sv.models import EspeceEchantillon


class ElementInfeste(models.Model):
    fiche_detection = models.ForeignKey(
        "sv.FicheDetection",
        on_delete=models.CASCADE,
        verbose_name="Fiche de détection",
        related_name="elements_infestes",
    )
    type = models.CharField("Type", choices=ElementInfesteType)
    espece = models.ForeignKey(
        EspeceEchantillon, on_delete=models.PROTECT, verbose_name="Espèce végétale", blank=True, null=True
    )
    quantite = models.CharField("Quantité d'éléments infestés", blank=True)
    quantite_unite = models.CharField("Unité", choices=ElementInfesteQuantiteUnite, blank=True)
    comments = models.TextField("Commentaire", blank=True)

    @property
    def quantite_with_unite(self):
        return f"{self.quantite} {self.get_quantite_unite_display()}" if self.quantite else ""

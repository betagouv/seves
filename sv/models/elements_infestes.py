from django.db import models

from sv.constants import ElementInfesteQuantiteUnite, ElementInfesteType
from sv.models import Prelevement


class ElementInfeste(models.Model):
    type = models.CharField("Type", choices=ElementInfesteType)
    espece = models.ForeignKey(Prelevement, on_delete=models.CASCADE)
    quantite = models.CharField("Quantité d'éléments infestés")
    quantite_unite = models.CharField("Quantité d'éléments infestés", choices=ElementInfesteQuantiteUnite)
    comments = models.TextField("Commentaires")

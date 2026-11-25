from django.core.validators import FileExtensionValidator
from django.db import models

from core.models import Structure


class Import(models.Model):
    file = models.FileField(
        upload_to="sa/imports/",
        verbose_name="Fichier",
        validators=[FileExtensionValidator(["csv"])],
    )
    nom_fichier = models.CharField(max_length=255, verbose_name="Nom du fichier importé")
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Import"
        verbose_name_plural = "Imports"

    def __str__(self):
        return f"Import du {self.date_creation:%d/%m/%Y %H:%M} par {self.createur}"

from django.db import models


class ResultatAnalyse(models.TextChoices):
    EN_ATTENTE = "en_attente", "En attente"
    DETECTE = "detecte", "Détecté"
    DETECTE_FAIBLE = "detecte_faible", "Détecté faible"
    NON_DETECTE = "non_detecte", "Non détecté"
    NON_INTERPRETABLE = "non_interpretable", "Non interprétable"


class Analyse(models.Model):
    evenement = models.ForeignKey(
        "sa.EvenementAnimal", on_delete=models.CASCADE, verbose_name="Événement", related_name="analyses"
    )
    maladie = models.ForeignKey("sa.Maladie", on_delete=models.PROTECT, verbose_name="Maladie", related_name="analyses")
    date_prelevement = models.DateField(verbose_name="Date du prélèvement")
    date_resultat = models.DateField(verbose_name="Date du résultat", blank=True, null=True)
    laboratoire = models.ForeignKey(
        "sa.Laboratoire", on_delete=models.PROTECT, verbose_name="Laboratoire", related_name="analyses"
    )
    methode = models.ForeignKey(
        "sa.MethodeAnalyse", on_delete=models.PROTECT, verbose_name="Méthode", related_name="analyses"
    )
    resultat = models.CharField(max_length=50, choices=ResultatAnalyse.choices, verbose_name="Résultat", null=False)
    resultat_confirmation = models.BooleanField(default=False, verbose_name="Résultat valant confirmation")

    class Meta:
        verbose_name = "Analyse"
        verbose_name_plural = "Analyses"

    def __str__(self):
        return f"{self.maladie.name} - {self.laboratoire.name}"

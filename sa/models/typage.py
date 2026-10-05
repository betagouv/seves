from django.db import models


class Typage(models.Model):
    maladie = models.ForeignKey(
        "sa.Maladie",
        on_delete=models.PROTECT,
        related_name="typages",
        verbose_name="Maladie",
    )
    valeur_niveau_2 = models.CharField(max_length=255, blank=True, verbose_name="Valeur (niveau 2)")
    valeur_niveau_3 = models.CharField(max_length=255, blank=True, verbose_name="Valeur (niveau 3)")

    class Meta:
        verbose_name = "Typage"
        verbose_name_plural = "Typages"
        ordering = ("maladie", "valeur_niveau_2", "valeur_niveau_3")
        constraints = [
            models.UniqueConstraint(
                fields=("maladie", "valeur_niveau_2", "valeur_niveau_3"),
                name="unique_typage_maladie_valeurs",
            ),
        ]

    def __str__(self):
        return f"{self.maladie.name} - {self.valeur_niveau_2} {self.valeur_niveau_3}".strip()

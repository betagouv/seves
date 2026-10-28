from django.db import models

TYPAGE_NIVEAU_2_VALUE_PREFIX = "typ-n-2-"
TYPAGE_NIVEAU_3_VALUE_PREFIX = "typ-n-3-"
NATURAL_SORT_COLLATION = "natural_sort"


class Typage(models.Model):
    maladie = models.ForeignKey(
        "sa.Maladie",
        on_delete=models.PROTECT,
        related_name="typages",
        verbose_name="Maladie",
    )
    valeur_niveau_2 = models.CharField(
        max_length=255, blank=True, db_collation=NATURAL_SORT_COLLATION, verbose_name="Valeur (niveau 2)"
    )
    valeur_niveau_3 = models.CharField(
        max_length=255, blank=True, db_collation=NATURAL_SORT_COLLATION, verbose_name="Valeur (niveau 3)"
    )

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

    @property
    def niveau_2_value(self):
        """Value shared by every typage of the same maladie and valeur_niveau_2, used in treeselect filters"""
        return f"{TYPAGE_NIVEAU_2_VALUE_PREFIX}{self.maladie_id}-{self.valeur_niveau_2}"

    @property
    def niveau_3_value(self):
        return f"{TYPAGE_NIVEAU_3_VALUE_PREFIX}{self.pk}"

    def __str__(self):
        return f"{self.maladie.name} - {self.valeur_niveau_2} {self.valeur_niveau_3}".strip()

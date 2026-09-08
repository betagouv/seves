from django.db import models


class LaboratoireType(models.TextChoices):
    AUTRE = (
        "autre",
        "Autre",
    )
    LNR = (
        "lnr",
        "LNR",
    )
    LDA = (
        "lda",
        "LDA",
    )


class Laboratoire(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom", unique=True)
    external_id = models.CharField(max_length=255, verbose_name="Référence hors seves", unique=True)
    code = models.CharField(max_length=255, verbose_name="Code", blank=True, null=True)
    laboratoire_type = models.CharField(
        max_length=255,
        choices=LaboratoireType.choices,
        verbose_name="Type de laboratoire",
        null=False,
    )

    def __str__(self):
        return self.name

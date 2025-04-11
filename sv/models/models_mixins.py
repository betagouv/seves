from django.db import models


class WithDerniereMiseAJourMixin(models.Model):
    date_derniere_mise_a_jour = models.DateTimeField(
        db_index=True,
        null=True,
        blank=True,
        auto_now=True,
        verbose_name="Date dernière mise à jour",
    )

    class Meta:
        abstract = True

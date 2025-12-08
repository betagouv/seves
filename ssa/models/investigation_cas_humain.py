import reversion
from django.db import models, transaction
from django.urls import reverse

from core.mixins import WithFreeLinkIdsMixin, AllowModificationMixin
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from ssa.constants import SourceInvestigationCasHumain
from ssa.managers import InvestigationCasHumainManager
from ssa.models.mixins import WithEvenementInformationMixin, WithEvenementRisqueMixin, WithSharedNumeroMixin


@reversion.register
class EvenementInvestigationCasHumain(
    AllowsSoftDeleteMixin,
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    WithSharedNumeroMixin,
    AllowModificationMixin,
    WithFreeLinkIdsMixin,
    models.Model,
):
    source = models.CharField(
        max_length=100, choices=SourceInvestigationCasHumain.choices, verbose_name="Source", blank=True
    )

    objects = InvestigationCasHumainManager()

    @property
    def numero(self):
        return f"A-{self.numero_annee}.{self.numero_evenement}"

    def __str__(self):
        return self.numero

    def get_update_url(self):
        return reverse("ssa:investigation-cas-humain-update", kwargs={"pk": self.pk})

    def get_absolute_url(self):
        return reverse("ssa:evenements-liste")  # Change when detail is implemented

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = self._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

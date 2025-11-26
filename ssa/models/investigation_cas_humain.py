import reversion
from django.db import models, transaction

from core.mixins import WithFreeLinkIdsMixin, AllowModificationMixin
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from ssa.constants import SourceInvestigationCasHumain
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

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = self._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

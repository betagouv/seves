import reversion
from django.db import models, transaction
from django.urls import reverse

from core.mixins import (
    WithFreeLinkIdsMixin,
    AllowModificationMixin,
    WithDocumentPermissionMixin,
    WithContactPermissionMixin,
    EmailNotificationMixin,
    WithMessageUrlsMixin,
)
from core.model_mixins import WithBlocCommunFieldsMixin
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from ssa.constants import SourceInvestigationCasHumain
from ssa.managers import InvestigationCasHumainManager
from ssa.models.mixins import (
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    WithSharedNumeroMixin,
    WithLatestVersionMixin,
    SsaBaseEvenementModel,
)


@reversion.register
class EvenementInvestigationCasHumain(
    SsaBaseEvenementModel,
    AllowsSoftDeleteMixin,
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    WithSharedNumeroMixin,
    WithLatestVersionMixin,
    AllowModificationMixin,
    WithBlocCommunFieldsMixin,
    WithDocumentPermissionMixin,
    WithContactPermissionMixin,
    WithFreeLinkIdsMixin,
    EmailNotificationMixin,
    WithMessageUrlsMixin,
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
        return reverse("ssa:investigation-cas-humain-details", kwargs={"pk": self.pk})

    def _user_can_interact(self, user):
        return not self.is_cloture and self.can_user_access(user)

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def get_email_subject(self):
        return f"{self.get_type_evenement_display()} {self.numero}"

    def get_short_email_display_name(self):
        return f"{self.get_type_evenement_display()} {self.numero}"

    def get_long_email_display_name(self):
        return f"{self.get_short_email_display_name()} {self.get_long_email_display_name_suffix()}"

    def get_long_email_display_name_as_html(self):
        return f"<b>{self.get_short_email_display_name()}</b> {self.get_long_email_display_name_suffix()}"

    def get_long_email_display_name_suffix(self):
        return f"(Danger : {self.get_categorie_danger_display() or 'Vide'})"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = self._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

import reversion
from django.db import models, transaction
from django.urls import reverse

from core.mixins import (
    WithFreeLinkIdsMixin,
    AllowModificationMixin,
    WithDocumentPermissionMixin,
    WithContactPermissionMixin,
)
from core.model_mixins import WithBlocCommunFieldsMixin
from core.models import Document
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from ssa.constants import SourceInvestigationCasHumain
from ssa.managers import InvestigationCasHumainManager
from ssa.models.mixins import (
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    WithSharedNumeroMixin,
    WithLatestVersionMixin,
)


@reversion.register
class EvenementInvestigationCasHumain(
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

    def get_message_form(self):
        from ssa.forms import MessageForm

        return MessageForm

    def get_allowed_document_types(self):
        return [
            Document.TypeDocument.SIGNALEMENT_CERFA,
            Document.TypeDocument.SIGNALEMENT_RASFF,
            Document.TypeDocument.SIGNALEMENT_AUTRE,
            Document.TypeDocument.RAPPORT_ANALYSE,
            Document.TypeDocument.ANALYSE_RISQUE,
            Document.TypeDocument.TRACABILITE_INTERNE,
            Document.TypeDocument.TRACABILITE_AVAL_RECIPIENT,
            Document.TypeDocument.TRACABILITE_AVAL_AUTRE,
            Document.TypeDocument.TRACABILITE_AMONT,
            Document.TypeDocument.DSCE_CHED,
            Document.TypeDocument.ETIQUETAGE,
            Document.TypeDocument.SUITES_ADMINISTRATIVES,
            Document.TypeDocument.COMMUNIQUE_PRESSE,
            Document.TypeDocument.CERTIFICAT_SANITAIRE,
            Document.TypeDocument.COURRIERS_COURRIELS,
            Document.TypeDocument.COMPTE_RENDU,
            Document.TypeDocument.PHOTO,
            Document.TypeDocument.AFFICHETTE_RAPPEL,
            Document.TypeDocument.AUTRE,
        ]

    def _user_can_interact(self, user):
        return not self.is_cloture and self.can_user_access(user)

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = self._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

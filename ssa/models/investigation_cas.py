import reversion
from django.utils.safestring import mark_safe
from reversion.models import Version

from core.mixins import (
    AllowsSoftDeleteMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithNumeroMixin,
    WithFreeLinkIdsMixin,
)
from core.model_mixins import WithBlocCommunFieldsMixin
from core.versions import get_versions_from_ids
from ssa.managers import InvestigationManager
from ssa.models.mixins import BaseSSAEvenement
from django.db import models, transaction


class SourceInvestigation(models.TextChoices):
    DO_LISTERIOSE = "do_listeriose", "DO Listériose"
    CAS_GROUPES = "cas_groupes", "Cas groupés"
    AUTRE = "autre", "Signalement autre"


@reversion.register()
class InvestigationCasHumain(
    AllowsSoftDeleteMixin,
    WithBlocCommunFieldsMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithNumeroMixin,
    WithFreeLinkIdsMixin,
    BaseSSAEvenement,
    models.Model,
):
    source = models.CharField(max_length=100, choices=SourceInvestigation.choices, verbose_name="Source", blank=True)

    objects = InvestigationManager()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = InvestigationCasHumain._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

    @property
    def numero(self):
        return f"I-{self.numero_annee}.{self.numero_evenement}"

    def __str__(self):
        return self.numero

    @property
    def readable_risk_fields(self):
        risk_fields = {
            "Catégorie de danger": self.get_categorie_danger_display(),
            "Précision danger": self.precision_danger,
            "Évaluation": mark_safe(self.evaluation.replace("\n", "<br>")),
            "Référence souche": self.reference_souches,
            "Référence cluster": self.reference_clusters,
        }
        return risk_fields

    @property
    def latest_version(self):
        from ssa.models import Etablissement

        etablissement_ids = [e.id for e in self.etablissements.all()]
        etablissements_versions = get_versions_from_ids(etablissement_ids, Etablissement)

        instance_version = (
            Version.objects.get_for_object(self)
            .select_related("revision")
            .select_related("revision__user__agent__structure")
            .first()
        )

        versions = list(etablissements_versions) + [instance_version]
        versions = [v for v in versions if v]
        if not versions:
            return None
        return max(versions, key=lambda obj: obj.revision.date_created)

    def can_user_access(self, user):
        if user.agent.is_in_structure(self.createur):
            return True
        return not self.is_draft

    def can_be_updated(self, user):
        return self._user_can_interact(user)

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def _user_can_interact(self, user):
        return not self.is_cloture and self.can_user_access(user)

    def get_email_subject(self):
        return f"{self.get_type_evenement_display()} {self.numero}"

    def get_message_form(self):
        from ssa.forms import MessageForm

        return MessageForm

    def get_soft_delete_success_message(self):
        return f"L'investigation {self.numero} a bien été supprimée"

    def get_soft_delete_confirm_title(self):
        return f"Supprimer l'investigation {self.numero}"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cette investigation ?"

    def get_publish_success_message(self):
        return "L'investigation produit publié avec succès"

    def get_publish_error_message(self):
        return "Cette investigation ne peut pas être publiée"

    def get_cloture_confirm_message(self):
        return f"L'investigation n°{self.numero} a bien été clôturée."

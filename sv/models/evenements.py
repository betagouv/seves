import datetime

import reversion
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.urls import reverse
from reversion.models import Version

from core.mixins import (
    AllowACNotificationMixin,
    WithVisibiliteMixin,
    WithMessageUrlsMixin,
    WithFreeLinkIdsMixin,
    AllowsSoftDeleteMixin,
    EmailNotificationMixin,
    WithDocumentPermissionMixin,
    WithContactPermissionMixin,
)
from core.mixins import WithEtatMixin
from core.model_mixins import WithBlocCommunFieldsMixin
from core.models import Structure, Document
from . import FicheZoneDelimitee
from .common import OrganismeNuisible, StatutReglementaire
from .models_mixins import WithDerniereMiseAJourMixin
from ..managers import EvenementManager


@reversion.register()
class Evenement(
    AllowACNotificationMixin,
    WithVisibiliteMixin,
    WithEtatMixin,
    WithMessageUrlsMixin,
    WithFreeLinkIdsMixin,
    AllowsSoftDeleteMixin,
    EmailNotificationMixin,
    WithDocumentPermissionMixin,
    WithContactPermissionMixin,
    WithDerniereMiseAJourMixin,
    WithBlocCommunFieldsMixin,
    models.Model,
):
    numero_annee = models.IntegerField(verbose_name="Année")
    numero_evenement = models.IntegerField(verbose_name="Numéro")
    organisme_nuisible = models.ForeignKey(
        OrganismeNuisible,
        on_delete=models.PROTECT,
        verbose_name="OEPP",
    )
    statut_reglementaire = models.ForeignKey(
        StatutReglementaire,
        on_delete=models.PROTECT,
        verbose_name="Statut règlementaire de l'organisme",
    )
    fiche_zone_delimitee = models.OneToOneField(
        FicheZoneDelimitee, on_delete=models.SET_NULL, verbose_name="Fiche zone delimitée", null=True, blank=True
    )
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    numero_europhyt = models.CharField(max_length=8, verbose_name="Numéro Europhyt", blank=True)
    numero_rasff = models.CharField(max_length=9, verbose_name="Numéro RASFF", blank=True)

    objects = EvenementManager()

    class Meta:
        verbose_name = "Évènement"
        verbose_name_plural = "Évènements"
        constraints = [
            models.UniqueConstraint(fields=["numero_annee", "numero_evenement"], name="unique_evenement_numero")
        ]

    @classmethod
    def _get_annee_and_numero(self):
        annee_courante = datetime.datetime.now().year
        last_fiche = (
            Evenement._base_manager.filter(numero_annee=annee_courante)
            .select_for_update()
            .order_by("-numero_evenement")
            .first()
        )
        numero_evenement = last_fiche.numero_evenement + 1 if last_fiche else 1
        return annee_courante, numero_evenement

    @property
    def numero(self):
        return f"{self.numero_annee}.{self.numero_evenement}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = Evenement._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("sv:evenement-details", kwargs={"numero": self.numero})

    def get_update_url(self):
        return reverse("sv:evenement-update", kwargs={"pk": self.pk})

    def get_visibilite_update_url(self):
        return reverse("sv:evenement-visibilite-update", kwargs={"pk": self.pk})

    def can_update_visibilite(self, user):
        return not self.is_draft and not self.is_cloture and user.agent.structure.is_mus_or_bsv

    def __str__(self):
        return f"{self.numero_annee}.{self.numero_evenement}"

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def can_be_deleted(self, user):
        return self.can_user_delete(user) and not self.is_cloture

    def soft_delete(self, user):
        if not self.can_user_delete(user):
            raise PermissionDenied

        if self.is_cloture:
            raise AttributeError("L'évènement ne peut pas être supprimé car il est clôturé")

        with transaction.atomic():
            for detection in self.detections.all():
                detection.soft_delete(user)
            self.is_deleted = True
            self.save()

    @property
    def latest_version(self):
        detections_latest_versions = [f.latest_version for f in self.detections.all()]
        zone_latest_version = self.fiche_zone_delimitee.latest_version if self.fiche_zone_delimitee else None
        instance_version = (
            Version.objects.get_for_object(self)
            .select_related("revision")
            .select_related("revision__user__agent__structure")
            .first()
        )

        versions = list(detections_latest_versions) + [zone_latest_version, instance_version]
        versions = [v for v in versions if v]
        if not versions:
            return None
        return max(versions, key=lambda obj: obj.revision.date_created)

    def get_publish_success_message(self):
        return f"Événement {self.numero} publié avec succès"

    def get_publish_error_message(self):
        return f"L'évènement {self.numero} ne peut pas être publié"

    def get_soft_delete_success_message(self):
        return f"L'évènement {self.numero} a bien été supprimé"

    def get_soft_delete_permission_error_message(self):
        return f"Vous n'avez pas les droits pour supprimer l'évènement {self.numero}"

    def get_soft_delete_attribute_error_message(self):
        return f"L'évènement {self.numero} ne peut pas être supprimé"

    def get_soft_delete_confirm_title(self):
        return f"Supprimer l'événement {self.numero}"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cet évènement ?"

    def get_cloture_confirm_message(self):
        return f"L'événement n°{self.numero} a bien été clôturé."

    def get_email_subject(self):
        return f"{self.organisme_nuisible.code_oepp} {self.numero}"

    def _user_can_interact(self, user):
        return not self.is_cloture and self.can_user_access(user)

    def can_be_updated(self, user):
        return self._user_can_interact(user)

    def can_add_fiche_detection(self, user):
        return self._user_can_interact(user)

    def can_delete_fiche_detection(self):
        return not self.is_cloture

    def can_update_fiche_detection(self, user):
        return self._user_can_interact(user)

    def can_delete_fiche_zone_delimitee(self, user):
        return False if not self.fiche_zone_delimitee else self.fiche_zone_delimitee.can_be_deleted(user)

    def can_update_fiche_zone_delimitee(self, user):
        return False if not self.fiche_zone_delimitee else self.fiche_zone_delimitee.can_be_updated(user)

    def can_add_fiche_zone_delimitee(self, user):
        return self._user_can_interact(user)

    def get_message_form(self):
        from ..forms import MessageForm

        return MessageForm

    def get_allowed_document_types(self):
        return [
            Document.TypeDocument.ARRETE,
            Document.TypeDocument.AUTRE,
            Document.TypeDocument.CARTOGRAPHIE,
            Document.TypeDocument.CERTIFICAT_PHYTOSANITAIRE,
            Document.TypeDocument.COMPTE_RENDU_REUNION,
            Document.TypeDocument.COURRIER_OFFICIEL,
            Document.TypeDocument.DSCE,
            Document.TypeDocument.FACTURE,
            Document.TypeDocument.IMAGE,
            Document.TypeDocument.PASSEPORT_PHYTOSANITAIRE,
            Document.TypeDocument.RAPPORT_ANALYSE,
            Document.TypeDocument.RAPPORT_INSPECTION,
            Document.TypeDocument.REGLEMENTATION,
            Document.TypeDocument.TRANSPORT,
            Document.TypeDocument.TRACABILITE,
        ]

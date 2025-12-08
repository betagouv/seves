from functools import cached_property

import reversion
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from reversion.models import Version

from core.soft_delete_mixins import AllowsSoftDeleteMixin
from core.models import Structure
from core.versions import get_versions_from_ids
from sv.managers import (
    FicheDetectionManager,
)
from .lieux import Lieu
from .prelevements import Prelevement
from .models_mixins import WithDerniereMiseAJourMixin
from ..validators import validate_numero_detection


class Contexte(models.Model):
    class Meta:
        verbose_name = "Contexte"
        verbose_name_plural = "Contextes"

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom


class StatutEvenement(models.Model):
    class Meta:
        verbose_name = "Statut de l'événement"
        verbose_name_plural = "Statuts de l'événement"
        db_table = "sv_statut_evenement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé", unique=True)

    def __str__(self):
        return self.libelle


@reversion.register()
class FicheDetection(
    AllowsSoftDeleteMixin,
    WithDerniereMiseAJourMixin,
    models.Model,
):
    class Meta:
        verbose_name = "Fiche détection"
        verbose_name_plural = "Fiches détection"
        db_table = "sv_fiche_detection"
        ordering = ["numero_detection"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(hors_zone_infestee__isnull=True) & Q(zone_infestee__isnull=True)
                    | Q(hors_zone_infestee__isnull=True) & Q(zone_infestee__isnull=False)
                    | Q(hors_zone_infestee__isnull=False) & Q(zone_infestee__isnull=True)
                ),
                name="check_hors_zone_infestee_or_zone_infestee_or_none",
            ),
        ]

    # Informations générales
    numero_detection = models.CharField(
        verbose_name="Numéro de détection", max_length=16, validators=[validate_numero_detection], unique=True
    )
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    statut_evenement = models.ForeignKey(
        StatutEvenement,
        on_delete=models.PROTECT,
        verbose_name="Statut de l'événement",
        blank=True,
        null=True,
    )
    contexte = models.ForeignKey(
        Contexte,
        on_delete=models.PROTECT,
        verbose_name="Contexte",
        blank=True,
        null=True,
    )
    date_premier_signalement = models.DateField(verbose_name="Date premier signalement", blank=True, null=True)
    commentaire = models.TextField(verbose_name="Commentaire", blank=True)

    # Mesures de gestion
    mesures_conservatoires_immediates = models.TextField(verbose_name="Mesures conservatoires immédiates", blank=True)
    mesures_consignation = models.TextField(verbose_name="Mesures de consignation", blank=True)
    mesures_phytosanitaires = models.TextField(verbose_name="Mesures phytosanitaires", blank=True)
    mesures_surveillance_specifique = models.TextField(verbose_name="Mesures de surveillance spécifique", blank=True)

    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    hors_zone_infestee = models.ForeignKey("FicheZoneDelimitee", on_delete=models.SET_NULL, null=True, blank=True)
    zone_infestee = models.ForeignKey("ZoneInfestee", on_delete=models.SET_NULL, null=True, blank=True)
    evenement = models.ForeignKey("Evenement", on_delete=models.PROTECT, null=False, related_name="detections")
    vegetaux_infestes = models.TextField(verbose_name="Nombre ou volume de végétaux infestés", blank=True)

    objects = FicheDetectionManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_state = {}
        self._original_state["hors_zone_infestee"] = self.hors_zone_infestee_id
        self._original_state["zone_infestee"] = self.zone_infestee_id

    def _save(self, *args, **kwargs):
        self._original_state["hors_zone_infestee"] = self.hors_zone_infestee_id
        self._original_state["zone_infestee"] = self.zone_infestee_id
        if not self.numero_detection:
            self.numero_detection = self.get_next_numero_detection()
        super().save(*args, **kwargs)

    @transaction.atomic
    def get_next_numero_detection(self):
        numero_detection = FicheDetection.objects.get_last_used_numero(self.evenement_id) + 1
        return f"{self.evenement.numero}.{numero_detection}"

    @property
    def numero(self):
        return self.numero_detection

    def _handle_hors_zone_infestee_change(self):
        from . import FicheZoneDelimitee

        if self.hors_zone_infestee_id and self._original_state["hors_zone_infestee"] is None:
            with transaction.atomic():
                with reversion.create_revision():
                    reversion.set_comment(f"La fiche détection '{self.pk}' a été ajoutée en hors zone infestée")
                    reversion.add_to_revision(self.hors_zone_infestee)
                FicheZoneDelimitee.objects.update_date_derniere_mise_a_jour(self.hors_zone_infestee.id)
        elif self._original_state["hors_zone_infestee"] and self.hors_zone_infestee_id is None:
            with transaction.atomic():
                fiche_zone_delimitee = FicheZoneDelimitee.objects.get(pk=self._original_state["hors_zone_infestee"])
                with reversion.create_revision():
                    reversion.set_comment(f"La fiche détection '{self.pk}' a été retirée en hors zone infestée")
                    reversion.add_to_revision(fiche_zone_delimitee)
                FicheZoneDelimitee.objects.update_date_derniere_mise_a_jour(fiche_zone_delimitee.id)

    def _handle_zone_infestee_change(self):
        from . import ZoneInfestee

        if self.zone_infestee_id and self._original_state["zone_infestee"] is None:
            with reversion.create_revision():
                reversion.set_comment(f"La fiche détection '{self.pk}' a été ajoutée en zone infestée")
                reversion.add_to_revision(self.zone_infestee)
        elif self._original_state["zone_infestee"] and self.zone_infestee_id is None:
            with reversion.create_revision():
                reversion.set_comment(f"La fiche détection '{self.pk}' a été retirée de la zone infestée")
                reversion.add_to_revision(ZoneInfestee.objects.get(pk=self._original_state["zone_infestee"]))

    def save(self, *args, **kwargs):
        need_revision = True
        if self.hors_zone_infestee_id != self._original_state["hors_zone_infestee"]:
            self._handle_hors_zone_infestee_change()
            self._save(*args, **kwargs)
            need_revision = False
        if self.zone_infestee_id != self._original_state["zone_infestee"]:
            self._handle_zone_infestee_change()
            self._save(*args, **kwargs)
            need_revision = False

        if need_revision:
            with reversion.create_revision():
                self._save(*args, **kwargs)

    def get_absolute_url(self):
        return self.evenement.get_absolute_url()

    def can_user_access(self, user):
        return self.evenement.can_user_access(user)

    def get_update_url(self):
        return reverse("sv:fiche-detection-modification", kwargs={"pk": self.pk})

    def can_user_delete(self, user):
        return self.evenement.can_user_access(user)

    def can_be_deleted(self, user):
        return self.can_user_delete(user) and not self.evenement.is_cloture

    def __str__(self):
        return self.numero

    @property
    def is_linked_to_fiche_zone_delimitee(self):
        return self.hors_zone_infestee is not None or self.zone_infestee is not None

    def get_fiche_zone_delimitee(self):
        if self.hors_zone_infestee:
            return self.hors_zone_infestee
        if self.zone_infestee and self.zone_infestee.fiche_zone_delimitee:
            return self.zone_infestee.fiche_zone_delimitee

    @cached_property
    def latest_version(self):
        lieu_versions = get_versions_from_ids([lieu.id for lieu in self.lieux.all()], Lieu)

        prelevements = Prelevement.objects.filter(lieu__fiche_detection__pk=self.pk).values_list("id", flat=True)
        prelevement_versions = get_versions_from_ids(prelevements, Prelevement)

        instance_version = (
            Version.objects.get_for_object(self).select_related("revision__user__agent__structure").first()
        )

        versions = list(lieu_versions) + list(prelevement_versions) + [instance_version]
        versions = [v for v in versions if v]
        if not versions:
            return None
        return max(versions, key=lambda obj: obj.revision.date_created)

    def get_soft_delete_success_message(self):
        return f"La détection {self.numero} a bien été supprimée"

    def get_soft_delete_permission_error_message(self):
        return f"Vous n'avez pas les droits pour supprimer la détection {self.numero}"

    def get_soft_delete_attribute_error_message(self):
        return f"La détection {self.numero} ne peut pas être supprimée"

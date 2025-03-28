import datetime

import reversion
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
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
)
from core.mixins import WithEtatMixin
from core.models import Document, Message, Contact, Structure, FinSuiviContact
from . import FicheZoneDelimitee
from .common import OrganismeNuisible, StatutReglementaire
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
    fin_suivi = GenericRelation(FinSuiviContact)

    documents = GenericRelation(Document)
    messages = GenericRelation(Message)
    contacts = models.ManyToManyField(Contact, verbose_name="Contacts", blank=True)

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

    def get_absolute_url_with_message(self, message_id: int):
        return f"{self.get_absolute_url()}?message={message_id}"

    def get_update_url(self):
        return reverse("sv:evenement-update", kwargs={"pk": self.pk})

    def get_visibilite_update_url(self):
        return reverse("sv:evenement-visibilite-update", kwargs={"pk": self.pk})

    def can_update_visibilite(self, user):
        return not self.is_draft and user.agent.structure.is_mus_or_bsv

    def __str__(self):
        return f"{self.numero_annee}.{self.numero_evenement}"

    def get_contacts_structures_not_in_fin_suivi(self):
        contacts_structure = self.contacts.exclude(structure__isnull=True).select_related("structure")
        fin_suivi_contacts_ids = self.fin_suivi.values_list("contact", flat=True)
        return contacts_structure.exclude(id__in=fin_suivi_contacts_ids)

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def soft_delete(self, user):
        if not self.can_user_delete(user):
            raise PermissionDenied

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

    def get_etat_data_for_contact(self, contact):
        content_type = ContentType.objects.get_for_model(self)
        is_fin_de_suivi = FinSuiviContact.objects.filter(content_type=content_type, object_id=self.pk)
        is_fin_de_suivi = is_fin_de_suivi.filter(contact=contact).exists()
        return self.get_etat_data_from_fin_de_suivi(is_fin_de_suivi)

    def get_etat_data_from_fin_de_suivi(self, is_fin_de_suivi):
        if not self.is_cloture() and is_fin_de_suivi:
            return {"etat": "fin de suivi", "readable_etat": "Fin de suivi"}
        return {"etat": self.etat, "readable_etat": self.get_etat_display()}

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

    def add_fin_suivi(self, user):
        with transaction.atomic():
            fin_suivi_contact = FinSuiviContact(
                content_object=self,
                contact=Contact.objects.get(structure=user.agent.structure),
            )
            fin_suivi_contact.full_clean()
            fin_suivi_contact.save()

            Message.objects.create(
                title="Fin de suivi",
                content="Fin de suivi ajoutée automatiquement suite à la clôture de l'événement.",
                sender=user.agent.contact_set.get(),
                message_type=Message.FIN_SUIVI,
                content_object=self,
            )

    def get_email_subject(self):
        return f"{self.organisme_nuisible.code_oepp} {self.numero}"

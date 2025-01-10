import reversion
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse

from core.mixins import (
    AllowACNotificationMixin,
    AllowVisibiliteMixin,
    WithMessageUrlsMixin,
    WithFreeLinkIdsMixin,
    AllowsSoftDeleteMixin,
)
from core.models import Document, Message, Contact, Visibilite, Structure, FinSuiviContact
from . import FicheZoneDelimitee
from .common import NumeroFiche, OrganismeNuisible, StatutReglementaire, Etat
from ..managers import EvenementManager
from ..mixins import WithEtatMixin


@reversion.register()
class Evenement(
    AllowACNotificationMixin,
    AllowVisibiliteMixin,
    WithEtatMixin,
    WithMessageUrlsMixin,
    WithFreeLinkIdsMixin,
    AllowsSoftDeleteMixin,
    models.Model,
):
    numero = models.OneToOneField(
        NumeroFiche, on_delete=models.PROTECT, verbose_name="Numéro de fiche", null=True, blank=True
    )
    organisme_nuisible = models.ForeignKey(
        OrganismeNuisible,
        on_delete=models.PROTECT,
        verbose_name="OEPP",
        blank=True,
        null=True,
    )
    statut_reglementaire = models.ForeignKey(
        StatutReglementaire,
        on_delete=models.PROTECT,
        verbose_name="Statut règlementaire de l'organisme",
        blank=True,
        null=True,
    )
    fiche_zone_delimitee = models.OneToOneField(
        FicheZoneDelimitee, on_delete=models.PROTECT, verbose_name="Fiche zone delimitée", null=True, blank=True
    )
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    etat = models.ForeignKey(
        Etat, on_delete=models.PROTECT, verbose_name="État de la fiche", default=Etat.get_etat_initial
    )
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
            models.CheckConstraint(
                check=~(Q(visibilite="brouillon") & Q(numero__isnull=False)),
                name="check_evenement_numero_fiche_is_null_when_visibilite_is_brouillon",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.numero and self.visibilite == Visibilite.LOCAL:
            self.numero = NumeroFiche.get_next_numero()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("evenement-details", kwargs={"pk": self.pk})

    def get_update_url(self):
        return reverse("evenement-update", kwargs={"pk": self.pk})

    def get_visibilite_update_url(self):
        return reverse("evenement-visibilite-update", kwargs={"pk": self.pk})

    def __str__(self):
        return str(self.numero)

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

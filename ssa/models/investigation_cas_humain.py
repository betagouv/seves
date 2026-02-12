from dirtyfields import DirtyFieldsMixin
from django.db import models, transaction
from django.urls import reverse
import reversion

from core.mixins import (
    AllowModificationMixin,
    EmailNotificationMixin,
    WithContactPermissionMixin,
    WithDocumentPermissionMixin,
    WithFreeLinkIdsMixin,
    WithMessageUrlsMixin,
)
from core.model_mixins import WithBlocCommunFieldsMixin
from core.models import LienLibre
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from ssa.constants import SourceInvestigationCasHumain
from ssa.managers import InvestigationCasHumainManager
from ssa.models.mixins import (
    SsaBaseEvenementModel,
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    WithLatestVersionMixin,
    WithSharedNumeroMixin,
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
    DirtyFieldsMixin,
    models.Model,
):
    source = models.CharField(
        max_length=100, choices=SourceInvestigationCasHumain.choices, verbose_name="Source", blank=True
    )

    historical_data = models.JSONField(default=dict, blank=True)

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

    def get_type_evenement_display(self):
        return "Investigation de cas humain"

    def get_soft_delete_success_message(self):
        return f"L'investigation de cas humain {self.numero} a bien été supprimée"

    def get_soft_delete_confirm_title(self):
        return f"Supprimer l'investigation de cas humain {self.numero}"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cette investigation de cas humain ?"

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

    def get_cloture_confirm_message(self):
        return f"L'événement n°{self.numero} a bien été clôturé."

    def get_email_cloture_text(self):
        return f"""
         Pour rappel, voici les éléments de synthèse pour cet évènement :
         - Créateur : {self.createur}
         - Date de création : {self.date_creation.strftime("%d/%m/%Y")}
         - N° RASFF/AAC : {self.numero_rasff}
         - Danger : {self.get_categorie_danger_display()}
         """

    def get_email_cloture_text_html(self):
        return f"""
         Pour rappel, voici les éléments de synthèse pour cet évènement
         <ul>
         <li>Créateur : {self.createur}</li>
         <li>Date de création : {self.date_creation.strftime("%d/%m/%Y")}</li>
         <li>N° RASFF/AAC : {self.numero_rasff}</li>
         <li>Danger : {self.get_categorie_danger_display()}</li>
         </ul>
         """

    @property
    def list_of_linked_objects_as_str(self):
        links = LienLibre.objects.for_object(self)
        objects = [link.related_object_1 if link.related_object_2 == self else link.related_object_2 for link in links]
        return [str(o) for o in objects if not o.is_deleted]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = self._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

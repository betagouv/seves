import reversion
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from reversion.models import Version

from core.mixins import (
    AllowsSoftDeleteMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithNumeroMixin,
    WithFreeLinkIdsMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
)
from core.model_mixins import WithBlocCommunFieldsMixin
from core.models import Structure, BaseEtablissement, Document
from tiac.constants import ModaliteDeclarationEvenement, EvenementOrigin, EvenementFollowUp
from .managers import EvenementSimpleManager


@reversion.register()
class EvenementSimple(
    AllowsSoftDeleteMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithNumeroMixin,
    WithFreeLinkIdsMixin,
    WithBlocCommunFieldsMixin,
    models.Model,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
):
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_reception = models.DateField(verbose_name="Date de réception à la DD(ETS)PP")
    evenement_origin = models.CharField(
        choices=EvenementOrigin.choices, verbose_name="Signalement déclaré par", blank=True
    )
    modalites_declaration = models.CharField(
        choices=ModaliteDeclarationEvenement.choices,
        default=ModaliteDeclarationEvenement.SIGNAL_CONSO,
        verbose_name="Modalités de déclaration",
        blank=True,
    )
    contenu = models.TextField(verbose_name="Contenu du signalement")
    notify_ars = models.BooleanField(default=False, verbose_name="ARS informée")
    nb_sick_persons = models.IntegerField(verbose_name="Nombre de malades total", null=True)

    follow_up = models.CharField(
        choices=EvenementFollowUp.choices, default=EvenementFollowUp.NONE, verbose_name="Suite donnée par la DD"
    )

    objects = EvenementSimpleManager()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = EvenementSimple._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

    @property
    def numero(self):
        return f"T-{self.numero_annee}.{self.numero_evenement}"

    def __str__(self):
        return self.numero

    def get_absolute_url(self):
        numero = f"{self.numero_annee}.{self.numero_evenement}"
        return reverse("tiac:evenement-simple-details", kwargs={"numero": numero})

    def can_user_access(self, user):
        if user.agent.is_in_structure(self.createur):
            return True
        return not self.is_draft

    @property
    def latest_version(self):
        return (
            Version.objects.get_for_object(self)
            .select_related("revision")
            .select_related("revision__user__agent__structure")
            .first()
        )

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def get_soft_delete_success_message(self):
        return f"L'évènement {self.numero} a bien été supprimé"

    def get_cloture_confirm_message(self):
        return f"L'événement n°{self.numero} a bien été clôturé."

    def get_soft_delete_confirm_title(self):
        return f"Supprimer l'événement {self.numero}"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cet évènement ?"

    def get_message_form(self):
        from tiac.forms import MessageForm

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

    def get_email_subject(self):
        return f"{self.numero}"


class Evaluation(models.TextChoices):
    SATISFAISANTE = "satisfaisante", "A - Maîtrise des risques satisfaisante"
    ACCEPTABLE = "acceptable", "B - Maîtrise des risques acceptable"
    MISE_EN_DEMEURE = "mise en demeure", "C - Maîtrise des risques insatisfaisante - Mise en demeure"
    RESTRICTION = "restriction", "C - Maîtrise des risques insatisfaisante - Restriction d'activité"
    PERTE_DE_MAITRISE = "perte de maitrise", "D - Perte de maîtrise des risques - Fermeture ou restriction d'activité"


@reversion.register()
class Etablissement(BaseEtablissement, models.Model):
    evenement_simple = models.ForeignKey(EvenementSimple, on_delete=models.PROTECT, related_name="etablissements")

    type_etablissement = models.CharField(max_length=45, verbose_name="Type d'établissement", blank=True)

    has_inspection = models.BooleanField(default=False, verbose_name="Inspection")
    numero_resytal = models.CharField(blank=True, verbose_name="Numéro Résytal")
    evaluation = models.CharField(choices=Evaluation.choices, blank=True, verbose_name="Évaluation globale")
    commentaire = models.TextField(verbose_name="Commentaire", blank=True)

    def __str__(self):
        return f"{self.raison_sociale}"

    def save(self, *args, **kwargs):
        with reversion.create_revision():
            super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(has_inspection=True) | (Q(numero_resytal="") & Q(evaluation="") & Q(commentaire=""))),
                name="inspection_required_for_inspection_related_fields",
            ),
        ]

    @property
    def address_summary(self):
        value = ""
        if self.commune:
            value = self.commune
        if self.departement:
            value += f" ({self.departement.numero}) | {self.departement.nom}"
        return value

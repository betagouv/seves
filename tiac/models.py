import reversion
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from reversion.models import Version

from core.mixins import (
    AllowsSoftDeleteMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithFreeLinkIdsMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
)
from core.model_mixins import WithBlocCommunFieldsMixin
from core.models import Structure, BaseEtablissement, Document, Departement
from ssa.models import CategorieProduit, CategorieDanger
from tiac.constants import (
    ModaliteDeclarationEvenement,
    EvenementOrigin,
    EvenementFollowUp,
    Motif,
    TypeRepas,
    TypeCollectivite,
    TypeAliment,
    MotifAliment,
    EtatPrelevement,
    DANGERS_COURANTS,
    SELECTED_HAZARD_CHOICES,
)
from .constants import DangersSyndromiques, SuspicionConclusion
from .managers import EvenementSimpleManager, InvestigationTiacManager
from .model_mixins import WithSharedNumeroMixin


class BaseTiacModel(models.Model):
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

    class Meta:
        abstract = True


@reversion.register()
class EvenementSimple(
    AllowsSoftDeleteMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithSharedNumeroMixin,
    WithFreeLinkIdsMixin,
    WithBlocCommunFieldsMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    BaseTiacModel,
    models.Model,
):
    nb_sick_persons = models.IntegerField(verbose_name="Nombre de malades total", null=True)

    follow_up = models.CharField(
        choices=EvenementFollowUp.choices, default=EvenementFollowUp.NONE, verbose_name="Suite donnée par la DD"
    )
    transfered_to = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name="transfered", null=True)

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

    def can_be_transfered(self, user):
        return self.can_user_access(user) and self.is_published

    def can_be_modified(self, user):
        return self.can_user_access(user) and not self.is_cloture

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

    def get_publish_success_message(self):
        return "Événement simple publié avec succès"

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


validate_resytal = RegexValidator(
    regex=r"^\d{2}-\d{6}$",
    message="Le numéro Resytal doit être au format AA-XXXXXX ; par exemple : 19-067409",
    code="invalid_resytal",
)


@reversion.register()
class Etablissement(BaseEtablissement, models.Model):
    evenement_simple = models.ForeignKey(
        EvenementSimple, null=True, default=None, on_delete=models.PROTECT, related_name="etablissements"
    )
    investigation = models.ForeignKey(
        "tiac.InvestigationTiac", null=True, default=None, on_delete=models.PROTECT, related_name="etablissements"
    )

    type_etablissement = models.CharField(max_length=45, verbose_name="Type d'établissement", blank=True)

    has_inspection = models.BooleanField(default=False, verbose_name="Inspection")
    numero_resytal = models.CharField(blank=True, verbose_name="Numéro Resytal", validators=[validate_resytal])
    date_inspection = models.DateField(blank=True, null=True, default=None, verbose_name="Date d'inspection")
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
                condition=(
                    Q(has_inspection=True)
                    | (Q(numero_resytal="") & Q(evaluation="") & Q(commentaire="") & Q(date_inspection=None))
                ),
                name="inspection_required_for_inspection_related_fields",
            ),
            models.CheckConstraint(
                condition=(
                    (Q(evenement_simple__isnull=True) & Q(investigation__isnull=False))
                    | (Q(evenement_simple__isnull=False) & Q(investigation__isnull=True))
                ),
                name="is_related_to_either_evenement_simple_or_investigation_tiac",
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


class TypeEvenement(models.TextChoices):
    INVESTIGATION_DD = "investigation par ma dd", "Investigation par ma DD"
    INVESTIGATION_COORDONNEE = "investigation coordonnée", "Investigation coordonnée / MUS informée"


class Analyses(models.TextChoices):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    INCONNU = "ne sait pas", "Ne sait pas"


@reversion.register()
class InvestigationTiac(
    AllowsSoftDeleteMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithSharedNumeroMixin,
    WithFreeLinkIdsMixin,
    WithBlocCommunFieldsMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    BaseTiacModel,
    models.Model,
):
    will_trigger_inquiry = models.BooleanField(default=False, verbose_name="Enquête auprès des cas")
    numero_sivss = models.CharField(
        max_length=6,
        verbose_name="N° SIVSS de l'ARS",
        blank=True,
        validators=[RegexValidator(r"^\d{6}$", "Doit contenir exactement 6 chiffres")],
    )
    type_evenement = models.CharField(
        max_length=100, choices=TypeEvenement.choices, verbose_name="Type d'événement", blank=True
    )

    # Cas
    nb_sick_persons = models.IntegerField(verbose_name="Nombre de malades total", null=True)
    nb_sick_persons_to_hospital = models.IntegerField(verbose_name="Dont conduits à l'hôpital", null=True)
    nb_dead_persons = models.IntegerField(verbose_name="Dont décédés", null=True)
    datetime_first_symptoms = models.DateTimeField(
        verbose_name="Première date et heure d'apparition des symptômes", null=True
    )
    datetime_last_symptoms = models.DateTimeField(
        verbose_name="Dernière date et heure d'apparition des symptômes", null=True
    )

    # Etiologie
    danger_syndromiques_suspectes = ArrayField(
        models.CharField(max_length=255, choices=DangersSyndromiques.choices),
        default=list,
        blank=True,
    )
    analyses_sur_les_malades = models.CharField(
        max_length=100, choices=Analyses.choices, verbose_name="Analyses engagées sur les malades", blank=True
    )
    precisions = models.CharField(max_length=255, verbose_name="Précisions", blank=True)

    agents_confirmes_ars = ArrayField(
        models.CharField(max_length=255, choices=CategorieDanger.choices),
        default=list,
        blank=True,
    )

    # Conclusion block
    suspicion_conclusion = models.CharField(
        "Conclusion de la suspicion de TIAC", choices=SuspicionConclusion, null=True, default=None, blank=True
    )
    selected_hazard = models.CharField(
        "Danger retenu",
        choices=SELECTED_HAZARD_CHOICES,
        default="",
        blank=True,
    )
    conclusion_comment = models.TextField("Commentaire", default="", blank=True)

    conclusion_etablissement = models.ForeignKey(
        "tiac.Etablissement", on_delete=models.PROTECT, null=True, default=None, blank=True
    )
    conclusion_repas = models.ForeignKey(
        "tiac.RepasSuspect", on_delete=models.PROTECT, null=True, default=None, blank=True
    )
    conclusion_aliment = models.ForeignKey(
        "tiac.AlimentSuspect", on_delete=models.PROTECT, null=True, default=None, blank=True
    )
    conclusion_analyse = models.ForeignKey(
        "tiac.AnalyseAlimentaire", on_delete=models.PROTECT, null=True, default=None, blank=True
    )

    objects = InvestigationTiacManager()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = InvestigationTiac._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

    def get_absolute_url(self):
        numero = f"{self.numero_annee}.{self.numero_evenement}"
        return reverse("tiac:investigation-tiac-details", kwargs={"numero": numero})

    def can_user_access(self, user):
        if user.agent.is_in_structure(self.createur):
            return True
        return not self.is_draft

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

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def get_soft_delete_success_message(self):
        return f"L'investigation TIAC {self.numero} a bien été supprimée"

    def get_soft_delete_permission_error_message(self):
        return "Vous n'avez pas les droits pour supprimer cette investigation"

    def get_soft_delete_attribute_error_message(self):
        return f"L'investigation {self.numero} ne peut pas être supprimé"

    def get_soft_delete_confirm_title(self):
        return "Supprimer l'événement"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cet événement ?"

    def get_cloture_confirm_message(self):
        return f"L'événement n°{self.numero} a bien été clôturé."

    def get_email_subject(self):
        return f"{self.numero}"

    @property
    def latest_version(self):
        return (
            Version.objects.get_for_object(self)
            .select_related("revision")
            .select_related("revision__user__agent__structure")
            .first()
        )

    def get_publish_success_message(self):
        return "Évènement publié avec succès"

    def __str__(self):
        return self.numero

    @property
    def numero(self):
        return f"T-{self.numero_annee}.{self.numero_evenement}"

    @property
    def type_evenement_display(self):
        if self.type_evenement == TypeEvenement.INVESTIGATION_DD:
            return "Invest. locale"
        if self.type_evenement == TypeEvenement.INVESTIGATION_COORDONNEE:
            return "Invest. coord. / MUS informée"
        return "-"

    @classmethod
    def danger_plus_courants(self):
        return DANGERS_COURANTS

    @property
    def short_conclusion_selected_hazard(self):
        if not self.selected_hazard:
            return ""
        return (
            DangersSyndromiques(self.selected_hazard).short_name
            if self.selected_hazard in DangersSyndromiques.values
            else CategorieDanger(self.selected_hazard).label
        )

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=(
                    models.Q(
                        suspicion_conclusion=SuspicionConclusion.CONFIRMED.value,
                        selected_hazard__in=CategorieDanger.values,
                    )
                    | models.Q(
                        suspicion_conclusion=SuspicionConclusion.SUSPECTED.value,
                        selected_hazard__in=DangersSyndromiques.values,
                    )
                    | (
                        ~models.Q(
                            suspicion_conclusion__in=[
                                SuspicionConclusion.SUSPECTED.value,
                                SuspicionConclusion.CONFIRMED.value,
                            ]
                        )
                        & models.Q(selected_hazard="")
                    )
                ),
                name="selected_hazard_constraints",
            ),
        )


class RepasSuspect(models.Model):
    investigation = models.ForeignKey(InvestigationTiac, on_delete=models.PROTECT, related_name="repas")
    denomination = models.CharField(max_length=255, verbose_name="Dénomination du repas")
    menu = models.TextField(verbose_name="Menu", blank=True)
    motif_suspicion = ArrayField(
        models.CharField(max_length=255, choices=Motif.choices),
        verbose_name="Motif de suspicion du repas",
        default=list,
        blank=True,
    )
    datetime_repas = models.DateTimeField(verbose_name="Date et heure du repas", blank=True, null=True)
    nombre_participant = models.IntegerField(verbose_name="Nombre de participant(e)s", blank=True, null=True)
    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        verbose_name="Département",
        blank=True,
        null=True,
    )
    type_repas = models.CharField(max_length=255, choices=TypeRepas.choices, blank=True)
    type_collectivite = models.CharField(max_length=255, choices=TypeCollectivite.choices, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(type_repas=TypeRepas.RESTAURATION_COLLECTIVE) | Q(type_collectivite="")),
                name="collectivite_only_if_repas_restauration_collective",
            )
        ]

    @property
    def motif_suspicion_labels(self):
        return ", ".join(Motif(m).label for m in self.motif_suspicion)

    @property
    def show_type_collectivite(self):
        return self.type_repas == TypeRepas.RESTAURATION_COLLECTIVE


class AlimentSuspect(models.Model):
    investigation = models.ForeignKey(InvestigationTiac, on_delete=models.PROTECT, related_name="aliments")
    denomination = models.CharField(max_length=255, verbose_name="Dénomination de l'aliment")
    type_aliment = models.CharField(max_length=255, choices=TypeAliment.choices, blank=True)

    description_composition = models.TextField(verbose_name="Description de la composition de l'aliment", blank=True)

    categorie_produit = models.CharField(
        max_length=255, choices=CategorieProduit.choices, verbose_name="Catégorie de produit", blank=True
    )
    description_produit = models.TextField(verbose_name="Description produit et emballage", blank=True)

    motif_suspicion = ArrayField(
        models.CharField(max_length=255, choices=MotifAliment.choices),
        verbose_name="Motif de suspicion de l'aliment",
        default=list,
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(type_aliment=TypeAliment.SIMPLE, description_composition="")
                | ~Q(type_aliment=TypeAliment.SIMPLE),
                name="produit_simple_constraint",
            ),
            models.CheckConstraint(
                check=Q(type_aliment=TypeAliment.CUISINE, categorie_produit="", description_produit="")
                | ~Q(type_aliment=TypeAliment.CUISINE),
                name="cuisiné_pas_de_categorie_emballage",
            ),
        ]

    @property
    def motif_suspicion_labels(self):
        return ", ".join(MotifAliment(m).label for m in self.motif_suspicion)

    @property
    def is_aliment_simple(self):
        return self.type_aliment == TypeAliment.SIMPLE

    @property
    def is_aliment_cuisine(self):
        return self.type_aliment == TypeAliment.CUISINE


class AnalyseAlimentaire(models.Model):
    investigation = models.ForeignKey(InvestigationTiac, on_delete=models.PROTECT, related_name="analyses_alimentaires")

    reference_prelevement = models.CharField("Référence du prélèvement")
    etat_prelevement = models.CharField("État du prélèvement", choices=EtatPrelevement.choices, blank=True)
    categorie_danger = ArrayField(
        models.CharField(max_length=255, choices=CategorieDanger.choices),
        default=list,
        blank=True,
    )
    comments = models.TextField("Commentaires liés à l’analyse", blank=True)
    sent_to_lnr_cnr = models.BooleanField("Envoyé au LNR/CNR")
    reference_souche = models.CharField("Référence souche", blank=True)

    @property
    def categorie_danger_labels(self):
        return [CategorieDanger(cd).label.split(">")[-1] for cd in self.categorie_danger]

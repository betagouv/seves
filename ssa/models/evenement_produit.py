import reversion
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from reversion.models import Version

from core.mixins import (
    WithEtatMixin,
    WithNumeroMixin,
    WithDocumentPermissionMixin,
    WithContactPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    AllowsSoftDeleteMixin,
    WithFreeLinkIdsMixin,
)
from core.model_mixins import WithBlocCommunFieldsMixin
from core.models import Structure, Document, LienLibre
from core.versions import get_versions_from_ids
from ssa.managers import EvenementProduitManager
from .categorie_produit import CategorieProduit
from ssa.models.validators import validate_numero_rasff, rappel_conso_validator
from .categorie_danger import CategorieDanger


class TypeEvenement(models.TextChoices):
    ALERTE_PRODUIT_NATIONALE = "alerte_produit_nationale", "Alerte produit nationale"
    ALERTE_PRODUIT_LOCALE = "alerte_produit_locale", "Alerte produit locale"
    NON_ALERTE = "non_alerte", "Non alerte"
    ALERTE_PRODUIT_UE = "alerte_produit_ue", "Alerte produit UE/INT (RASFF)"
    NON_ALERTE_UE = "non_alerte_ue", "Non alerte UE/INT (AAC)"
    INVESTIGATION_CAS_HUMAINS = "investigation_cas_humain", "Investigation cas humains"
    AUTRE_ACTION_COORDONNEE = "autre_action_coordonnee", "Autre action coordonnée"


class Source(models.TextChoices):
    AUTOCONTROLE_NOTIFIE_PRODUIT = "autocontrole_notifie_produit", "Autocontrôle notifié (produit)"
    AUTOCONTROLE_NOTIFIE_ENVIRONNEMENT = "autocontrole_notifie_environnement", "Autocontrôle notifié (environnement)"
    PRELEVEMENT_PSPC = "prelevement_pspc", "Prélèvement PSPC"
    AUTRE_PRELEVEMENT_OFFICIEL = "autre_prelevement_officiel", "Autre prélèvement officiel"
    AUTRE_CONSTAT_OFFICIEL = "autre_constat_officiel", "Autre constat officiel"
    INVESTIGATION_CAS_HUMAINS = "investigation_cas_humains", "Investigation de cas humains"
    DO_LISTERIOSE = "do_listeriose", "DO Listériose"
    CAS_GROUPES = "cas_groupes", "Cas groupés"
    SIGNALEMENT_CONSOMMATEUR = "signalement_consommateur", "Signalement consommateur"
    AUTRE = "autre", "Signalement autre"


class PretAManger(models.TextChoices):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    SANS_OBJET = "sans_objet", "Sans objet"


class TemperatureConservation(models.TextChoices):
    REFRIGERE = "refrigere", "Réfrigéré"
    SURGELE = "surgele", "Surgelé"
    TEMPERATURE_AMBIANTE = "temperature_ambiante", "Température ambiante"


class ActionEngagees(models.TextChoices):
    PAS_DE_MESURE = "pas_de_mesure", "Pas de mesure de retrait ou rappel"
    RETRAIT = "retrait_marche", "Retrait du marché (sans information des consommateurs)"
    RETRAIT_RAPPEL = "retrait_rappel", "Retrait et rappel"
    RETRAIT_RAPPEL_CP = "retrait_rappel_communique_presse", "Retrait et rappel avec communiqué de presse"


class QuantificationUnite(models.TextChoices):
    CM = "cm", "cm"
    MM = "mm", "mm"
    DEG_C = "°C", "°C"
    PH = "pH", "pH"
    AW = "Aw", "Aw"
    G = "g", "g"
    MG = "mg", "mg"
    MG_G = "mg/g", "mg/g"
    MGEQ_G = "mgeq/g", "mgeq/g"
    UG_G = "µg/g", "µg/g"
    NG_G = "ng/g", "ng/g"
    G_100G = "g/100 g", "g/100 g"
    MG_100G = "mg/100 g", "mg/100 g"
    G_KG = "g/kg", "g/kg"
    MG_KG = "mg/kg", "mg/kg"
    UG_KG = "µg/kg", "µg/kg"
    NG_KG = "ng/kg", "ng/kg"
    PG_KG = "pg/kg", "pg/kg"
    PAR_1G = "/1 g", "/1 g"
    PAR_10G = "/10 g", "/10 g"
    PAR_25G = "/25 g", "/25 g"
    PAR_100G = "/100 g", "/100 g"
    PAR_KG = "/kg", "/kg"
    UFC = "UFC", "UFC"
    UFC_G = "UFC/g", "UFC/g"
    UFC_10G = "UFC/10 g", "UFC/10 g"
    UFC_25G = "UFC/25 g", "UFC/25 g"
    UFC_ML = "UFC/mL", "UFC/mL"
    NPP_100G = "NPP/100 g", "NPP/100 g"
    ML = "mL", "mL"
    MMOL_L = "mmol/L", "mmol/L"
    UL_L = "µL/L", "µL/L"
    ML_100ML = "mL/100 mL", "mL/100 mL"
    PAR_ML = "/mL", "/mL"
    PAR_100ML = "/100 mL", "/100 mL"
    PAR_250ML = "/250 mL", "/250 mL"
    UL_KG = "µL/kg", "µL/kg"
    MMOL_KG = "mmol/kg", "mmol/kg"
    ML_10G = "mL/10 g", "mL/10 g"
    ML_100G = "mL/100 g", "mL/100 g"
    UL_G = "µL/g", "µL/g"
    G_ML = "g/mL", "g/mL"
    G_L = "g/L", "g/L"
    MG_L = "mg/L", "mg/L"
    UG_L = "µg/L", "µg/L"
    G_100ML = "g/100 mL", "g/100 mL"
    MG_100ML = "mg/100 mL", "mg/100 mL"
    POURCENT_25G = "%/25 g", "%/25 g"
    POURCENT_100G = "%/100 g", "%/100 g"
    POURCENT = "%", "%"
    POUR_MILLE = "‰", "‰"
    BQ_KG = "bq/kg", "bq/kg"
    AUTRE = "autre unite", "autre unité"

    @classmethod
    def with_opt_group(cls):
        most_used = [cls.MG_KG, cls.UG_KG, cls.UFC_G, cls.PAR_10G, cls.PAR_25G, cls.NPP_100G]
        return [
            ("Unités courantes", [(c.value, c.label) for c in most_used]),
            ("Autres unités", [(c.value, c.label) for c in cls]),
        ]


@reversion.register()
class EvenementProduit(
    AllowsSoftDeleteMixin,
    WithBlocCommunFieldsMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithNumeroMixin,
    WithFreeLinkIdsMixin,
    models.Model,
):
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    numero_rasff = models.CharField(
        max_length=9, verbose_name="N° RASFF/AAC", blank=True, validators=[validate_numero_rasff]
    )

    # Informations générales
    type_evenement = models.CharField(max_length=100, choices=TypeEvenement.choices, verbose_name="Type d'événement")
    source = models.CharField(max_length=100, choices=Source.choices, verbose_name="Source", blank=True)
    description = models.TextField(verbose_name="Description de l'événement")

    # Informations liées au produit
    categorie_produit = models.CharField(
        max_length=255, choices=CategorieProduit.choices, verbose_name="Catégorie de produit", blank=True
    )
    denomination = models.CharField(max_length=255, verbose_name="Dénomination", blank=True)
    marque = models.CharField(max_length=255, verbose_name="Marque", blank=True)
    lots = models.TextField(blank=True, verbose_name="Lots, DLC/DDM")
    description_complementaire = models.TextField(blank=True, verbose_name="Description complémentaire")
    temperature_conservation = models.CharField(
        max_length=100, choices=TemperatureConservation.choices, verbose_name="Température de conservation"
    )

    # Informations liées au risque
    categorie_danger = models.CharField(
        max_length=255, choices=CategorieDanger.choices, verbose_name="Catégorie de danger", blank=True
    )
    precision_danger = models.CharField(blank=True, max_length=255, verbose_name="Précision danger")
    quantification = models.CharField(
        blank=True, null=True, verbose_name="Quantification maximale à l'origine de l'événement"
    )
    quantification_unite = models.CharField(
        blank=True, max_length=100, choices=QuantificationUnite.choices, verbose_name="Unité"
    )
    evaluation = models.TextField(blank=True, verbose_name="Évaluation")
    produit_pret_a_manger = models.CharField(
        blank=True, max_length=100, choices=PretAManger.choices, verbose_name="Produit Prêt à manger (PAM)"
    )
    reference_souches = models.CharField(max_length=255, verbose_name="Références souches", blank=True)
    reference_clusters = models.CharField(max_length=255, verbose_name="Références clusters", blank=True)

    actions_engagees = models.CharField(max_length=100, choices=ActionEngagees.choices, verbose_name="Action engagées")

    numeros_rappel_conso = ArrayField(
        models.CharField(max_length=12, validators=[rappel_conso_validator]), blank=True, null=True
    )

    objects = EvenementProduitManager()

    SOURCES_FOR_HUMAN_CASE = [Source.DO_LISTERIOSE, Source.CAS_GROUPES]

    def get_absolute_url(self):
        return reverse("ssa:evenement-produit-details", kwargs={"numero": self.numero})

    def get_update_url(self):
        return reverse("ssa:evenement-produit-update", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with reversion.create_revision():
                if not self.numero_annee and not self.numero_evenement:
                    annee, numero = EvenementProduit._get_annee_and_numero()
                    self.numero_annee = annee
                    self.numero_evenement = numero
                super().save(*args, **kwargs)

    def __str__(self):
        return self.numero

    @property
    def product_description(self):
        product_description = ""
        if self.denomination:
            product_description = f"{self.denomination} "
        if self.marque:
            product_description += f"{self.marque} "
        if self.description_complementaire:
            product_description += f"{self.description_complementaire}"
        return product_description.strip()

    @property
    def readable_product_fields(self):
        return {
            "Catégorie": self.get_categorie_produit_display(),
            "Dénomination": self.denomination,
            "Marque": self.marque,
            "Lots, DLC/DDM": mark_safe(self.lots.replace("\n", "<br>")),
            "Description complémentaire": mark_safe(self.description_complementaire.replace("\n", "<br>")),
            "Température de conservation": self.get_temperature_conservation_display(),
        }

    @property
    def readable_risk_fields(self):
        quantification = None
        if self.quantification:
            quantification = f"{self.quantification} {self.get_quantification_unite_display()}"

        risk_fields = {
            "Catégorie de danger": self.get_categorie_danger_display(),
            "Précision danger": self.precision_danger,
            "Résultat analytique du danger": quantification,
            "Évaluation": mark_safe(self.evaluation.replace("\n", "<br>")),
            "Produit prêt à manger (PAM)": self.get_produit_pret_a_manger_display(),
            "Référence souche": self.reference_souches,
            "Référence cluster": self.reference_clusters,
        }

        if not self.categorie_danger or self.categorie_danger not in CategorieDanger.dangers_bacteriens():
            risk_fields.pop("Produit prêt à manger (PAM)")
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

    @classmethod
    def danger_plus_courants(self):
        return [
            CategorieDanger.LISTERIA_MONOCYTOGENES,
            CategorieDanger.SALMONELLA,
            CategorieDanger.E_COLI_NON_STEC,
            CategorieDanger.PESTICIDE_RESIDU,
        ]

    @property
    def list_of_linked_objects_as_str(self):
        links = LienLibre.objects.for_object(self)
        objects = [link.related_object_1 if link.related_object_2 == self else link.related_object_2 for link in links]
        return [str(o) for o in objects if not o.is_deleted]

    def can_user_access(self, user):
        if user.agent.is_in_structure(self.createur):
            return True
        return not self.is_draft

    def can_be_updated(self, user):
        return self._user_can_interact(user)

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def get_soft_delete_success_message(self):
        return f"L'évènement {self.numero} a bien été supprimé"

    def get_soft_delete_confirm_title(self):
        return f"Supprimer l'événement {self.numero}"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cet évènement ?"

    def get_publish_success_message(self):
        return "Événement produit publié avec succès"

    def get_publish_error_message(self):
        return "Cet événement produit ne peut pas être publié"

    def _user_can_interact(self, user):
        return not self.is_cloture and self.can_user_access(user)

    def get_email_subject(self):
        return f"{self.get_type_evenement_display()} {self.numero}"

    def get_cloture_confirm_message(self):
        return f"L'événement n°{self.numero} a bien été clôturé."

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
            Document.TypeDocument.AUTRE,
        ]

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(source=Source.AUTRE)
                    | models.Q(source="")
                    | (
                        models.Q(type_evenement=TypeEvenement.INVESTIGATION_CAS_HUMAINS)
                        & models.Q(source__in=[Source.DO_LISTERIOSE, Source.CAS_GROUPES])
                    )
                    | (
                        ~models.Q(type_evenement=TypeEvenement.INVESTIGATION_CAS_HUMAINS)
                        & ~models.Q(source__in=[Source.DO_LISTERIOSE, Source.CAS_GROUPES])
                    )
                ),
                name="type_evenement_source_constraint",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(produit_pret_a_manger="")
                    | models.Q(categorie_danger__in=CategorieDanger.dangers_bacteriens())
                ),
                name="pam_requires_danger_bacterien",
            ),
        ]

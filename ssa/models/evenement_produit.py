import reversion
from dirtyfields import DirtyFieldsMixin
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.mixins import (
    WithDocumentPermissionMixin,
    WithContactPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    WithFreeLinkIdsMixin,
    AllowModificationMixin,
)
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from core.model_mixins import WithBlocCommunFieldsMixin, EmailableObjectMixin
from core.models import LienLibre
from ssa.managers import EvenementProduitManager
from ssa.models.validators import rappel_conso_validator
from ..constants import CategorieDanger, CategorieProduit, Source, TypeEvenement
from .mixins import (
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    WithSharedNumeroMixin,
    WithLatestVersionMixin,
    SsaBaseEvenementModel,
)


class TemperatureConservation(models.TextChoices):
    REFRIGERE = "refrigere", "Réfrigéré"
    SURGELE = "surgele", "Surgelé"
    TEMPERATURE_AMBIANTE = "temperature_ambiante", "Température ambiante"


class ActionEngagees(models.TextChoices):
    PAS_DE_MESURE = "pas_de_mesure", "Pas de mesure de retrait ou rappel"
    RETRAIT = "retrait_marche", "Retrait du marché sans information des consommateurs"
    RETRAIT_RAPPEL = "retrait_rappel", "Retrait et information du consommateur / rappel "
    RETRAIT_RAPPEL_CP = "retrait_rappel_communique_presse", "Retrait et rappel avec communiqué de presse"
    RETRAIT_CONTROLE = "retrait_rappel_controle_effectivite", "Retrait et rappel avec contrôle de l'effectivité"


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


@reversion.register(follow=["contacts"])
class EvenementProduit(
    SsaBaseEvenementModel,
    AllowsSoftDeleteMixin,
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    WithBlocCommunFieldsMixin,
    WithLatestVersionMixin,
    WithDocumentPermissionMixin,
    WithMessageUrlsMixin,
    EmailNotificationMixin,
    WithContactPermissionMixin,
    AllowModificationMixin,
    WithSharedNumeroMixin,
    WithFreeLinkIdsMixin,
    EmailableObjectMixin,
    DirtyFieldsMixin,
    models.Model,
):
    # WithEvenementInformationMixin
    type_evenement = models.CharField(max_length=100, choices=TypeEvenement.choices, verbose_name="Type d'événement")
    aliments_animaux = models.BooleanField(null=True, verbose_name="Inclut des aliments pour animaux")

    # Informations liées au produit
    categorie_produit = models.CharField(
        max_length=255, choices=CategorieProduit.choices, verbose_name="Catégorie de produit", blank=True
    )
    denomination = models.CharField(max_length=255, verbose_name="Dénomination", blank=True)
    marque = models.CharField(max_length=255, verbose_name="Marque", blank=True)
    lots = models.TextField(blank=True, verbose_name="Lots, DLC/DDM")
    description_complementaire = models.TextField(blank=True, verbose_name="Description complémentaire")
    temperature_conservation = models.CharField(
        max_length=100, choices=TemperatureConservation.choices, verbose_name="Température de conservation", blank=True
    )

    # Informations liées au risque
    # Inclue WithEvenementRisqueMixin
    source = models.CharField(max_length=100, choices=Source.choices, verbose_name="Source", blank=True)
    quantification = models.CharField(
        blank=True, null=True, verbose_name="Quantification maximale à l'origine de l'événement"
    )
    quantification_unite = models.CharField(
        blank=True, max_length=100, choices=QuantificationUnite.choices, verbose_name="Unité"
    )

    actions_engagees = models.CharField(max_length=100, choices=ActionEngagees.choices, verbose_name="Action engagées")

    numeros_rappel_conso = ArrayField(
        models.CharField(max_length=12, validators=[rappel_conso_validator]), blank=True, null=True
    )

    historical_data = models.JSONField(default=dict, blank=True)

    objects = EvenementProduitManager()

    def get_absolute_url(self):
        return reverse("ssa:evenement-produit-details", kwargs={"pk": self.pk})

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

    @property
    def numero(self):
        return f"A-{self.numero_annee}.{self.numero_evenement}"

    def __str__(self):
        return self.numero

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

    @classmethod
    def danger_plus_courants(self):
        return [
            CategorieDanger.LISTERIA_MONOCYTOGENES,
            CategorieDanger.SALMONELLA_ENTERITIDIS,
            CategorieDanger.SALMONELLA_TYPHIMURIUM,
            CategorieDanger.ESCHERICHIA_COLI_SHIGATOXINOGENE,
            CategorieDanger.RESIDU_DE_PESTICIDE_BIOCIDE,
        ]

    @property
    def list_of_linked_objects_as_str(self):
        links = LienLibre.objects.for_object(self)
        objects = [link.related_object_1 if link.related_object_2 == self else link.related_object_2 for link in links]
        return [str(o) for o in objects if not o.is_deleted]

    def can_be_updated(self, user):
        return self._user_can_interact(user)

    def can_be_downloaded(self, user):
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

    def get_short_email_display_name(self):
        return f"{self.get_type_evenement_display()} {self.numero}"

    def get_long_email_display_name(self):
        return f"{self.get_short_email_display_name()} {self.get_long_email_display_name_suffix()}"

    def get_long_email_display_name_as_html(self):
        return f"<b>{self.get_short_email_display_name()}</b> {self.get_long_email_display_name_suffix()}"

    def get_long_email_display_name_suffix(self):
        return f"(Catégorie de produit : {self.get_categorie_produit_display() or 'Vide'} / Danger : {self.get_categorie_danger_display() or 'Vide'})"

    def get_email_cloture_text(self):
        return f"""
        Pour rappel, voici les éléments de synthèse pour cet évènement :
        - Créateur : {self.createur}
        - Date de création : {self.date_creation.strftime("%d/%m/%Y")}
        - N° RASFF/AAC : {self.numero_rasff}
        - Catégorie produit : {self.get_categorie_produit_display()}
        - Danger : {self.get_categorie_danger_display()}
        """

    def get_email_cloture_text_html(self):
        return f"""
        Pour rappel, voici les éléments de synthèse pour cet évènement
        <ul>
        <li>Créateur : {self.createur}</li>
        <li>Date de création : {self.date_creation.strftime("%d/%m/%Y")}</li>
        <li>N° RASFF/AAC : {self.numero_rasff}</li>
        <li>Catégorie produit : {self.get_categorie_produit_display()}</li>
        <li>Danger : {self.get_categorie_danger_display()}</li>
        </ul>
        """

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(produit_pret_a_manger="")
                    | models.Q(categorie_danger__in=CategorieDanger.dangers_bacteriens())
                ),
                name="pam_requires_danger_bacterien",
            ),
        ]

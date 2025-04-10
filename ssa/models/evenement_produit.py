import reversion
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.urls import reverse
from reversion.models import Version

from core.mixins import WithEtatMixin, WithNumeroMixin
from core.models import Structure
from core.versions import get_versions_from_ids
from ssa.models.validators import validate_numero_rasff, rappel_conso_validator


class TypeEvenement(models.TextChoices):
    ALERTE_PRODUIT_NATIONALE = "alerte_produit_nationale", "Alerte produit nationale"
    ALERTE_PRODUIT_LOCALE = "alerte_produit_locale", "Alerte produit locale"
    NON_ALERTE = "non_alerte", "Non alerte"
    ALERTE_PRODUIT_UE = "alerte_produit_ue", "Alerte produit UE/INT (RASFF)"
    NON_ALERTE_UE = "non_alerte_ue", "Non alerte UE/INT (AAC)"
    INVESTIGATION_CAS_HUMAINS = "investigation_cas_humain", "Investigation cas humains"


class Source(models.TextChoices):
    AUTOCONTROLE = "autocontrole", "Autocontrôle"
    PRELEVEMENT_PSPC = "prelevement_pspc", "Prélèvement PSPC"
    PRELEVEMENT_SIVEP = "prelevement_sivep", "Prélèvemeent SIVEP"
    AUTRE_PRELEVEMENT_OFFICIEL = "autre_prelevement_officiel", "Autre prélèvement officiel"
    AUTRE_CONSTAT_OFFICIEL = "autre_constat_officiel", "Autre constat officiel"
    SUSPICION_TIAC = "suspicion_tiac", "Suspicion de TIAC"
    INVESTIGATION_CAS_HUMAINS = "investigation_cas_humains", "Investigation de cas humains"
    DO_LISTERIOSE = "do_listeriose", "DO Listériose"
    CAS_GROUPES = "cas_groupes", "Cas groupés"
    TIACS = "tiacs", "TIACS"
    AUTRE = "autre", "Autre"


class CerfaRecu(models.TextChoices):
    OUI_PRODUIT = "oui_produit", "Oui produit"
    OUI_ENVIRONNEMENT = "oui_environnement", "Oui environnement"
    NON = "non", "Non"


class PretAManger(models.TextChoices):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    NON_APPLICABLE = "non_applicable", "Non applicable"


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
    PAR_100G = "/100g", "/100g"


@reversion.register()
class EvenementProduit(WithEtatMixin, WithNumeroMixin, models.Model):
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    numero_rasff = models.CharField(
        max_length=9, verbose_name="N° RASFF/AAC", blank=True, validators=[validate_numero_rasff]
    )

    # Informations générales
    type_evenement = models.CharField(max_length=100, choices=TypeEvenement.choices, verbose_name="Type d'événement")
    source = models.CharField(max_length=100, choices=Source.choices, verbose_name="Source", blank=True)
    cerfa_recu = models.CharField(
        max_length=100, choices=CerfaRecu.choices, verbose_name="Cerfa reçu du professionnel ?", blank=True
    )
    description = models.TextField(verbose_name="Description de l'événement")

    # Informations liées au produit
    denomination = models.CharField(max_length=255, verbose_name="Dénomination")
    marque = models.CharField(max_length=255, verbose_name="Marque", blank=True)
    lots = models.TextField(blank=True, verbose_name="Lots, DLC/DDM")
    description_complementaire = models.TextField(blank=True, verbose_name="Description complémentaire")
    temperature_conservation = models.CharField(
        max_length=100, choices=TemperatureConservation.choices, verbose_name="Température de conservation"
    )

    # Informations liées au risque
    quantification = models.FloatField(
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

    SOURCES_FOR_HUMAN_CASE = [Source.DO_LISTERIOSE, Source.CAS_GROUPES, Source.TIACS]

    def get_absolute_url(self):
        return reverse("ssa:evenement-produit-details", kwargs={"numero": self.numero})

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
    def readable_product_fields(self):
        return {
            "Dénomination": self.denomination,
            "Marque": self.marque,
            "Lots, DLC/DDM": self.lots,
            "Description complémentaire": self.description_complementaire,
            "Température de conservation": self.get_temperature_conservation_display(),
        }

    @property
    def readable_risk_fields(self):
        return {
            "Quantification": f"{self.quantification} {self.get_quantification_unite_display()}",
            "Évaluation": self.evaluation,
            "Produit prêt à manger (PAM)": self.get_produit_pret_a_manger_display(),
            "Référence souche": self.reference_souches,
            "Référence cluster": self.reference_clusters,
        }

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

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(source=Source.AUTRE)
                    | models.Q(source="")
                    | (
                        models.Q(type_evenement=TypeEvenement.INVESTIGATION_CAS_HUMAINS)
                        & models.Q(source__in=[Source.DO_LISTERIOSE, Source.CAS_GROUPES, Source.TIACS])
                    )
                    | (
                        ~models.Q(type_evenement=TypeEvenement.INVESTIGATION_CAS_HUMAINS)
                        & ~models.Q(source__in=[Source.DO_LISTERIOSE, Source.CAS_GROUPES, Source.TIACS])
                    )
                ),
                name="type_evenement_source_constraint",
            ),
        ]

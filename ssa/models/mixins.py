from django.db import models
from django.utils import timezone
from reversion.models import Version
from core.versions import get_versions_from_ids

from core.mixins import sort_tree, WithNumeroMixin
from core.models import Structure, Document
from ssa.constants import CategorieDanger
from ssa.models.validators import validate_numero_rasff


def build_combined_options(*enums, sorted_results=False):
    all_options = []
    for enum in enums:
        all_options.extend(enum.build_options(sorted_results=False))
    if sorted_results:
        sort_tree(all_options)
    return all_options


class WithEvenementInformationMixin(models.Model):
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_reception = models.DateField(verbose_name="Date de réception")
    numero_rasff = models.CharField(
        max_length=9, verbose_name="N° RASFF/AAC", blank=True, validators=[validate_numero_rasff]
    )

    # Informations générales
    description = models.TextField(verbose_name="Description de l'événement")

    class Meta:
        abstract = True


class WithEvenementRisqueMixin(models.Model):
    categorie_danger = models.CharField(
        max_length=255, choices=CategorieDanger.choices, verbose_name="Catégorie de danger", blank=True
    )
    precision_danger = models.CharField(blank=True, max_length=255, verbose_name="Précision danger")
    evaluation = models.TextField(blank=True, verbose_name="Évaluation")
    reference_souches = models.CharField(max_length=255, verbose_name="Références souches", blank=True)
    reference_clusters = models.CharField(max_length=255, verbose_name="Références clusters", blank=True)

    class Meta:
        abstract = True


class WithLatestVersionMixin(models.Model):
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
        abstract = True


class WithSharedNumeroMixin(WithNumeroMixin):
    @classmethod
    def _get_annee_and_numero(cls):
        from . import EvenementInvestigationCasHumain, EvenementProduit

        annee_courante = timezone.now().year

        def last_num(model):
            fiche = (
                model._base_manager.filter(numero_annee=annee_courante)
                .select_for_update()
                .order_by("-numero_evenement")
                .first()
            )
            return fiche.numero_evenement if fiche else 0

        numero = max(last_num(EvenementInvestigationCasHumain), last_num(EvenementProduit)) + 1
        return annee_courante, numero

    class Meta:
        abstract = True


class SsaBaseEvenementModel(models.Model):
    def get_crdi_form(self):
        from ssa.forms import CompteRenduDemandeInterventionForm

        return CompteRenduDemandeInterventionForm

    @property
    def limit_contacts_to_user_from_app(self):
        return "ssa"

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

    class Meta:
        abstract = True

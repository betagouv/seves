from django.db import models
from django.utils import timezone

from core.mixins import sort_tree, WithNumeroMixin
from core.models import Structure
from ssa.constants import CategorieDanger, TypeEvenement
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
    type_evenement = models.CharField(max_length=100, choices=TypeEvenement.choices, verbose_name="Type d'événement")
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

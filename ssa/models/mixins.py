from django.db import models

from core.mixins import sort_tree
from core.models import Structure
from ssa.constants import CategorieDanger, TypeEvenement, Source
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
    source = models.CharField(max_length=100, choices=Source.choices, verbose_name="Source", blank=True)
    description = models.TextField(verbose_name="Description de l'événement")
    aliments_animaux = models.BooleanField(null=True, verbose_name="Inclut des aliments pour animaux")

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

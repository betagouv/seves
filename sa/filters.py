from functools import reduce
from operator import or_

from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from django.forms import Media, TextInput
from django.utils.functional import lazy
import django_filters
from dsfr.forms import DsfrBaseForm

from core.filters_mixins import WithDatePublicationFilterMixin, WithEtatFilterMixin, WithNumeroFilterMixin
from core.form_mixins import js_module
from core.models import Departement, Region
from core.widgets import TreeselectCheckbox, TreeselectGroup, TreeselectItem, TreeselectRadio
from sa.forms.especes_concernees import EspeceTreeselectRadio
from sa.models.evenement import StatutEvenement

from .models import Espece, EvenementAnimal, Maladie

REGION_VALUE_PREFIX = "region-"


def _departement_choices():
    return [(departement.numero, str(departement)) for departement in Departement.objects.order_by("numero")] + [
        (f"{REGION_VALUE_PREFIX}{region.pk}", region.nom) for region in Region.objects.all()
    ]


def _departement_treeselect_choices():
    departements_by_region = {}
    for departement in Departement.objects.select_related("region").order_by("region__nom", "numero"):
        departements_by_region.setdefault(departement.region, []).append(
            TreeselectItem(value=departement.numero, label=str(departement), categorised_label=str(departement))
        )
    return tuple(
        TreeselectGroup(
            value=f"{REGION_VALUE_PREFIX}{region.pk}",
            label=region.nom,
            categorised_label=region.nom,
            choices=departements,
        )
        for region, departements in departements_by_region.items()
    )


class EvenementAnimalFilterForm(DsfrBaseForm):
    @property
    def media(self):
        return super().media + Media(
            js=(js_module("sa/espece_autres.mjs"), js_module("sa/evenement_list.mjs")),
        )

    @property
    def autres_especes(self):
        return Espece.autres_for_virtual_list()


class EvenementAnimalFilter(
    WithNumeroFilterMixin,
    WithDatePublicationFilterMixin,
    WithEtatFilterMixin,
    django_filters.FilterSet,
):
    numero = django_filters.CharFilter(
        method="filter_numero",
        label="N° de fiche",
        widget=TextInput(attrs={"placeholder": "Ex : 12"}),
    )
    maladie = django_filters.ModelChoiceFilter(
        label="Maladie",
        queryset=Maladie.objects.all(),
        widget=TreeselectRadio(
            choices=Maladie.treeselect_choices,
            attrs={"placeholder": "Rechercher", "min_search_length": 2},
        ),
    )
    espece = django_filters.ModelChoiceFilter(
        label="Espèce",
        queryset=Espece.objects.all(),
        widget=EspeceTreeselectRadio(attrs={"placeholder": "Rechercher"}),
    )
    statut = django_filters.ChoiceFilter(
        label="Statut",
        field_name="statut_evenement",
        choices=sorted(StatutEvenement.choices, key=lambda choice: choice[1]),
        empty_label="Tous",
    )
    full_text_search = django_filters.CharFilter(
        method="filter_full_text_search",
        label="Recherche libre",
        widget=TextInput(attrs={"placeholder": "Tous champs"}),
    )
    departement = django_filters.MultipleChoiceFilter(
        label="Département",
        method="filter_departement",
        choices=_departement_choices,
        widget=TreeselectCheckbox(
            choices=lazy(_departement_treeselect_choices, tuple)(),
            attrs={"placeholder": "Rechercher", "min_search_length": 2},
        ),
    )
    numero_adis = django_filters.CharFilter(label="N° ADIS", lookup_expr="icontains")
    commune = django_filters.CharFilter(
        method="filter_commune",
        label="Commune du foyer",
        widget=TextInput(attrs={"placeholder": "Ex : Challans"}),
    )

    class Meta:
        model = EvenementAnimal
        fields = [
            "annee",
            "maladie",
            "numero",
            "espece",
            "statut",
            "start_date",
            "end_date",
            "full_text_search",
            "departement",
            "numero_adis",
            "commune",
            "etat",
        ]
        form = EvenementAnimalFilterForm

    def filter_numero(self, queryset, name, value):
        value = value.strip()
        if value.isdigit():
            return queryset.filter(numero_evenement__contains=value)

        # Search with the complete event number (e.g. "FCO-2026.12")
        return queryset.annotate(
            numero_complet=Concat(
                "maladie__acronym",
                Value("-"),
                "numero_annee",
                Value("."),
                "numero_evenement",
                output_field=CharField(),
            )
        ).filter(numero_complet__icontains=value)

    def filter_full_text_search(self, queryset, name, value):
        return queryset.search(value)

    def filter_departement(self, queryset, name, value):
        """
        Departement of the foyer, deduced from its code INSEE (as the localisation has no departement field).
        """
        region_ids = [v.removeprefix(REGION_VALUE_PREFIX) for v in value if v.startswith(REGION_VALUE_PREFIX)]
        numeros = {v for v in value if not v.startswith(REGION_VALUE_PREFIX)}
        numeros.update(Departement.objects.filter(region__in=region_ids).values_list("numero", flat=True))
        if not numeros:
            return queryset
        return queryset.filter(reduce(or_, (Q(code_insee__startswith=numero) for numero in numeros)))

    def filter_commune(self, queryset, name, value):
        value = value.strip()
        return queryset.filter(Q(commune__unaccent__icontains=value) | Q(code_insee__istartswith=value))

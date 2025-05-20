import django_filters
from django.forms import DateInput, TextInput

from core.filters_mixins import WithNumeroFilterMixin
from core.forms import DSFRForm
from ssa.models import EvenementProduit
from ssa.models.departements import Departement
from django_countries import Countries
from django_filters.filters import BaseInFilter, CharFilter


class StrInFilter(BaseInFilter, CharFilter):
    pass


class EvenementProduitFilterForm(DSFRForm):
    manual_render_fields = [
        "etat",
        "temperature_conservation",
        "produit_pret_a_manger",
        "reference_souches",
        "reference_clusters",
        "actions_engagees",
        "numeros_rappel_conso",
        "numero_agrement",
        "commune",
        "departement",
        "pays",
    ]


class EvenementProduitFilter(WithNumeroFilterMixin, django_filters.FilterSet):
    numero_rasff = django_filters.CharFilter(
        label="Numéro RASFF/AAC",
        widget=TextInput(
            attrs={
                "placeholder": "0000.0000 ou 000000",
                "pattern": "^(\d{4}\.\d{4}|AA\d{2}\.\d{4}|\d{6})$",
                "title": "Le format attendu est XXXX.YYYY ou AAXX.YYYY ou XXXXXX (ex: 2025.1234 ou AA24.1234 ou 123456)",
            }
        ),
    )
    start_date = django_filters.DateFilter(
        field_name="date_creation__date",
        lookup_expr="gte",
        label="Période du",
        widget=DateInput(attrs={"type": "date"}),
    )
    end_date = django_filters.DateFilter(
        field_name="date_creation__date", lookup_expr="lte", label="Au", widget=DateInput(attrs={"type": "date"})
    )
    full_text_search = django_filters.CharFilter(
        method="filter_full_text_search",
        label="Recherche libre",
        widget=TextInput(attrs={"placeholder": "Description, produit, établissement..."}),
    )

    numeros_rappel_conso = StrInFilter(
        field_name="numeros_rappel_conso", lookup_expr="overlap", distinct=True, label="Rappel Conso"
    )

    numero_agrement = django_filters.CharFilter(
        field_name="etablissements__numero_agrement", distinct=True, label="Numéro d'agrément"
    )
    commune = django_filters.CharFilter(field_name="etablissements__commune", distinct=True, label="Commune")
    departement = django_filters.ChoiceFilter(
        choices=Departement, field_name="etablissements__departement", distinct=True, label="Département"
    )
    pays = django_filters.ChoiceFilter(
        choices=Countries, field_name="etablissements__pays", distinct=True, label="Pays"
    )

    class Meta:
        model = EvenementProduit
        fields = [
            "numero",
            "numero_rasff",
            "start_date",
            "end_date",
            "type_evenement",
            "full_text_search",
            "etat",
            "temperature_conservation",
            "produit_pret_a_manger",
            "reference_souches",
            "reference_clusters",
            "actions_engagees",
            "numeros_rappel_conso",
            "numero_agrement",
            "commune",
            "departement",
            "pays",
        ]
        form = EvenementProduitFilterForm

    def filter_full_text_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.search(value)

import django_filters
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db.models import Q
from django.forms import DateInput, TextInput, CheckboxInput
from django_countries import Countries
from django_filters.filters import BaseInFilter, CharFilter
from queryset_sequence import QuerySetSequence

from core.filters_mixins import (
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
    WithAgentContactFilterMixin,
    WithEtatFilterMixin,
)
from core.forms import DSFRForm
from core.models import LienLibre, Departement
from ssa.constants import TypeEvenement, SourceInvestigationCasHumain, Source
from ssa.models import EvenementProduit


class StrInFilter(BaseInFilter, CharFilter):
    pass


class CharInFilter(CharFilter):
    def filter(self, qs, value):
        if isinstance(value, str):
            value = [v.strip() for v in value.split("||") if v.strip()]
        return super().filter(qs, value)


class EvenementProduitFilterForm(DSFRForm):
    manual_render_fields = [
        "etat",
        "aliments_animaux",
        "temperature_conservation",
        "produit_pret_a_manger",
        "reference_souches",
        "reference_clusters",
        "actions_engagees",
        "numeros_rappel_conso",
        "siret",
        "numero_agrement",
        "commune",
        "departement",
        "pays",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type_evenement"].choices = [(k, v) for k, v in TypeEvenement.choices] + [
            ("ich", "Investigation de cas humain")
        ]
        self.fields["source"].choices = list(dict.fromkeys(Source.choices + SourceInvestigationCasHumain.choices))


class WithEtablissementFilterMixin(django_filters.FilterSet):
    siret = django_filters.CharFilter(
        field_name="etablissements__siret", lookup_expr="contains", distinct=True, label="Siren/Siret"
    )
    commune = django_filters.CharFilter(field_name="etablissements__commune", distinct=True, label="Commune")
    departement = django_filters.ModelChoiceFilter(
        label="Département",
        queryset=Departement.objects.order_by("numero").all(),
        empty_label=settings.SELECT_EMPTY_CHOICE,
        field_name="etablissements__departement",
        distinct=True,
    )
    pays = django_filters.ChoiceFilter(
        choices=Countries, field_name="etablissements__pays", distinct=True, label="Pays"
    )


class EvenementFilter(
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
    WithAgentContactFilterMixin,
    WithEtablissementFilterMixin,
    WithEtatFilterMixin,
    django_filters.FilterSet,
):
    with_free_links = django_filters.BooleanFilter(
        label="Inclure les liaisons", method="filter_with_free_links", widget=CheckboxInput
    )
    numero_rasff = django_filters.CharFilter(
        label="Numéro RASFF/AAC",
        lookup_expr="contains",
        widget=TextInput(
            attrs={
                "placeholder": "0000.0000 ou 000000",
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
    type_evenement = django_filters.ChoiceFilter(
        label="Type d'événement ", choices=[], empty_label=settings.SELECT_EMPTY_CHOICE, method="filter_type_evenement"
    )
    source = django_filters.ChoiceFilter(label="Source ", choices=[], empty_label=settings.SELECT_EMPTY_CHOICE)
    full_text_search = django_filters.CharFilter(
        method="filter_full_text_search",
        label="Recherche libre",
        widget=TextInput(attrs={"placeholder": "Description, produit, établissement..."}),
    )

    aliments_animaux = django_filters.ChoiceFilter(
        field_name="aliments_animaux",
        label="Inclut des aliments pour animaux",
        choices=(
            (True, "Oui"),
            (False, "Non"),
            ("inconnu", "Inconnu"),
        ),
        method="filter_aliments_animaux",
    )
    numeros_rappel_conso = StrInFilter(
        field_name="numeros_rappel_conso", lookup_expr="overlap", distinct=True, label="Rappel Conso"
    )
    numero_agrement = django_filters.CharFilter(
        field_name="etablissements__numero_agrement", distinct=True, label="Numéro d'agrément"
    )
    categorie_produit = CharInFilter(field_name="categorie_produit", lookup_expr="in")
    categorie_danger = CharInFilter(field_name="categorie_danger", lookup_expr="in")

    class Meta:
        model = EvenementProduit
        fields = [
            "numero",
            "with_free_links",
            "numero_rasff",
            "categorie_produit",
            "categorie_danger",
            "structure_contact",
            "agent_contact",
            "type_evenement",
            "source",
            "start_date",
            "end_date",
            "full_text_search",
            "etat",
            "aliments_animaux",
            "temperature_conservation",
            "produit_pret_a_manger",
            "reference_souches",
            "reference_clusters",
            "actions_engagees",
            "numeros_rappel_conso",
            "siret",
            "numero_agrement",
            "commune",
            "departement",
            "pays",
        ]
        form = EvenementProduitFilterForm

    def filter_type_evenement(self, queryset, name, value):
        if value == "ich":
            if issubclass(queryset.model, EvenementProduit):
                queryset = queryset.none()
        else:
            if issubclass(queryset.model, EvenementProduit):
                queryset = queryset.filter(type_evenement=value)
            else:
                queryset = queryset.none()
        return queryset

    def filter_full_text_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.search(value)

    def filter_with_free_links(self, queryset, name, value):
        return queryset

    def filter_aliments_animaux(self, queryset, name, value):
        if not issubclass(queryset.model, EvenementProduit):
            return queryset.none()
        if value == "inconnu":
            return queryset.filter(aliments_animaux__isnull=True)
        return queryset.filter(aliments_animaux=value)

    def filter_structure_contact(self, queryset, name, value):
        return (
            super().filter_structure_contact(queryset, name, value)
            if issubclass(queryset.model, EvenementProduit)
            else queryset.none()
        )

    def filter_agent_contact(self, queryset, name, value):
        return (
            super().filter_agent_contact(queryset, name, value)
            if issubclass(queryset.model, EvenementProduit)
            else queryset.none()
        )

    def with_free_links_filtered(self, ids):
        queryset = self.queryset
        subquerysets = queryset._querysets if isinstance(queryset, QuerySetSequence) else [queryset]
        content_types = set(ContentType.objects.get_for_models(*[queryset.model for queryset in subquerysets]).values())

        for idx, subqueryset in enumerate(subquerysets):
            objects_from_free_links_1 = LienLibre.objects.filter(
                content_type_2__in=content_types, content_type_1__in=content_types, object_id_1__in=ids
            ).values_list("object_id_2", flat=True)
            objects_from_free_links_2 = LienLibre.objects.filter(
                content_type_1__in=content_types, content_type_2__in=content_types, object_id_2__in=ids
            ).values_list("object_id_1", flat=True)
            subquerysets[idx] = subqueryset.filter(
                Q(id__in=ids) | Q(id__in=objects_from_free_links_1) | Q(id__in=objects_from_free_links_2)
            ).distinct()

        if isinstance(queryset, QuerySetSequence):
            queryset._set_querysets(subquerysets)
            return queryset
        else:
            return subquerysets[0]

    def filter_queryset(self, queryset):
        with_free_links = self.form.cleaned_data.get("with_free_links")

        if not isinstance(queryset, QuerySetSequence):
            queryset = super().filter_queryset(queryset)
            return self.with_free_links_filtered(queryset.values_list("id", flat=True)) if with_free_links else queryset

        querysets = queryset._querysets
        for idx, subqueryset in enumerate(querysets):
            for name, value in self.form.cleaned_data.items():
                try:
                    subqueryset = self.filters[name].filter(subqueryset, value)
                except FieldError:
                    subqueryset = subqueryset.none()
                    break
            querysets[idx] = subqueryset

        if not with_free_links:
            queryset._set_querysets(querysets)
            return queryset

        ids = []
        for subqueryset in querysets:
            ids.extend(subqueryset.values_list("id", flat=True))

        return self.with_free_links_filtered(ids)

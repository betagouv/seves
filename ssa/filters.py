from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db.models import Q
from django.forms import CheckboxInput, TextInput
from django_countries import Countries
import django_filters
from django_filters.filters import BaseInFilter, CharFilter, MultipleChoiceFilter
from dsfr.forms import DsfrBaseForm
from queryset_sequence import QuerySetSequence

from core.filters_mixins import (
    WithAgentContactFilterMixin,
    WithDatePublicationFilterMixin,
    WithDateReceptionFilterMixin,
    WithEtatFilterMixin,
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
)
from core.models import Departement, LienLibre
from core.widgets import TreeselectCheckbox
from ssa.constants import CategorieDanger, CategorieProduit, Source, SourceInvestigationCasHumain, TypeEvenement
from ssa.models import EvenementProduit


class StrInFilter(BaseInFilter, CharFilter):
    pass


class CharInFilter(CharFilter):
    def filter(self, qs, value):
        if isinstance(value, str):
            value = [v.strip() for v in value.split("||") if v.strip()]
        return super().filter(qs, value)


class EvenementProduitFilterForm(DsfrBaseForm):
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
    numero_agrement = django_filters.CharFilter(
        field_name="etablissements__numero_agrement", distinct=True, label="Numéro d'agrément"
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
    WithDatePublicationFilterMixin,
    WithDateReceptionFilterMixin,
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
    type_evenement = django_filters.MultipleChoiceFilter(
        label="Type d'événement ",
        choices=[(k, v) for k, v in TypeEvenement.choices] + [("ich", "Investigation de cas humain")],
        method="filter_type_evenement",
        widget=TreeselectCheckbox(choices=(), attrs={"placeholder": "Rechercher"}),
    )
    source = django_filters.MultipleChoiceFilter(
        label="Source",
        choices=(Source.choices + SourceInvestigationCasHumain.choices),
        widget=TreeselectCheckbox(choices=(), attrs={"placeholder": "Rechercher"}),
    )
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
        ),
        method="filter_aliments_animaux",
    )
    numeros_rappel_conso = StrInFilter(
        field_name="numeros_rappel_conso", lookup_expr="overlap", distinct=True, label="Rappel Conso"
    )
    categorie_produit = MultipleChoiceFilter(
        field_name="categorie_produit",
        choices=CategorieProduit,
        widget=TreeselectCheckbox(choices=CategorieProduit.treeselect_groups),
        label="Catégorie de produit",
    )
    categorie_danger = MultipleChoiceFilter(
        field_name="categorie_danger",
        choices=CategorieDanger,
        widget=TreeselectCheckbox(choices=CategorieDanger.treeselect_groups),
        label="Catégorie de danger",
    )
    reference_souches = django_filters.CharFilter(lookup_expr="icontains")
    reference_clusters = django_filters.CharFilter(lookup_expr="icontains")

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
            "start_date_reception",
            "end_date_reception",
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
        is_produit = issubclass(queryset.model, EvenementProduit)

        if is_produit:
            types_evenements = [v for v in value if v != "ich"]
            return queryset.filter(type_evenement__in=types_evenements) if types_evenements else queryset.none()

        return queryset if "ich" in value else queryset.none()

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

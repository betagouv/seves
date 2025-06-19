import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import DateInput, TextInput
from django_countries import Countries
from django_filters.filters import BaseInFilter, CharFilter

from core.fields import DSFRCheckboxInput
from core.filters_mixins import WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin
from core.forms import DSFRForm
from core.models import LienLibre
from ssa.models import EvenementProduit
from ssa.models.departements import Departement


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


class EvenementProduitFilter(
    WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin, django_filters.FilterSet
):
    with_free_links = django_filters.BooleanFilter(
        label="", method="filter_with_free_links", widget=DSFRCheckboxInput(label="Inclure les liaisons")
    )
    numero_rasff = django_filters.CharFilter(
        label="Numéro RASFF/AAC",
        widget=TextInput(
            attrs={
                "placeholder": "0000.0000 ou 000000",
                "pattern": r"^(\d{4}\.\d{4}|AA\d{2}\.\d{4}|\d{6})$",
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
    siret = django_filters.CharFilter(
        field_name="etablissements__siret", lookup_expr="contains", distinct=True, label="Siren/Siret"
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
            "start_date",
            "end_date",
            "full_text_search",
            "etat",
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

    def filter_full_text_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.search(value)

    def filter_with_free_links(self, queryset, name, value):
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if self.form.cleaned_data["with_free_links"] is True:
            ids = queryset.values_list("id", flat=True)

            content_type = ContentType.objects.get_for_model(EvenementProduit)
            objects_from_free_links_1 = LienLibre.objects.filter(
                content_type_2=content_type, content_type_1=content_type, object_id_1__in=ids
            ).values_list("object_id_2", flat=True)
            objects_from_free_links_2 = LienLibre.objects.filter(
                content_type_1=content_type, content_type_2=content_type, object_id_2__in=ids
            ).values_list("object_id_1", flat=True)
            queryset = self.queryset.filter(
                Q(id__in=ids) | Q(id__in=objects_from_free_links_1) | Q(id__in=objects_from_free_links_2)
            ).distinct()

        return queryset

from functools import reduce
from operator import or_

from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from django.forms import DateInput, Media, RadioSelect, TextInput
from django.utils.functional import lazy
import django_filters
from dsfr.forms import DsfrBaseForm

from core.filters_mixins import WithDatePublicationFilterMixin, WithEtatFilterMixin, WithNumeroFilterMixin
from core.form_mixins import js_module
from core.mixins import WithEtatMixin, normalize
from core.models import Departement, Region
from core.widgets import TreeselectCheckbox, TreeselectGroup, TreeselectItem, TreeselectRadio
from sa.forms.especes_concernees import EspeceTreeselectRadio
from sa.models.analyse import Analyse, ResultatAnalyse
from sa.models.evenement import ContexteSuspicion, StatutAnimal, StatutEvenement, TypeDetenteur, TypeLieu
from sa.models.veterinaire import Veterinaire

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


class DateRangeFilter(django_filters.DateFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", DateInput(attrs={"type": "date"}))
        super().__init__(*args, **kwargs)


class InlineRadioSelect(RadioSelect):
    inline = True

    def format_value(self, value):
        return super().format_value(value) or [""]


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

    # Advanced filters
    etat = django_filters.ChoiceFilter(
        method="filter_etat",
        label="État",
        choices=(
            (WithEtatMixin.Etat.BROUILLON, WithEtatMixin.Etat.BROUILLON.label),
            (WithEtatMixin.Etat.EN_COURS, WithEtatMixin.Etat.EN_COURS.label),
            ("fin de suivi", "Fin de suivi"),
            (WithEtatMixin.Etat.CLOTURE, WithEtatMixin.Etat.CLOTURE.label),
        ),
        empty_label="Tous",
    )
    start_date_confirmation = DateRangeFilter(method="filter_date_confirmation", label="Date de confirmation entre le")
    end_date_confirmation = DateRangeFilter(method="filter_date_confirmation", label="et le")
    resultat_confirmation = django_filters.ChoiceFilter(
        method="filter_resultat_confirmation",
        label="Résultat de confirmation",
        choices=ResultatAnalyse.choices,
        empty_label="Tous",
    )
    context_suspicion = django_filters.ChoiceFilter(
        label="Contexte de la suspicion",
        choices=ContexteSuspicion.choices,
        empty_label="Tous",
    )
    start_date_first_symptoms = DateRangeFilter(
        field_name="date_first_symptoms", lookup_expr="gte", label="Date des premiers symptômes entre le"
    )
    end_date_first_symptoms = DateRangeFilter(field_name="date_first_symptoms", lookup_expr="lte", label="et le")

    type_detenteur = django_filters.ChoiceFilter(
        method="filter_type_detenteur",
        label="Type de détenteur",
        choices=TypeDetenteur.choices,
        empty_label="Tous",
        widget=InlineRadioSelect,
    )
    numero_identifiant_detenteur = django_filters.CharFilter(
        method="filter_numero_identifiant_detenteur",
        label="N° identifiant",
        widget=TextInput(attrs={"placeholder": "INUAV, EDE, EGET, SIRET…"}),
    )
    commune_detenteur = django_filters.CharFilter(method="filter_commune_detenteur", label="Commune")
    nom_detenteur = django_filters.CharFilter(method="filter_nom_detenteur", label="Nom / raison sociale")

    type_lieu = django_filters.ChoiceFilter(
        label="Type de lieu",
        choices=sorted(TypeLieu.choices, key=lambda choice: normalize(choice[1])),
        empty_label="Tous les types de lieu",
    )

    veterinaire = django_filters.CharFilter(
        method="filter_veterinaire",
        label="Structure ou vétérinaire",
        widget=TextInput(attrs={"placeholder": "Nom de la structure ou du vétérinaire"}),
    )
    numero_dpe = django_filters.CharFilter(method="filter_numero_dpe", label="N° DPE")

    start_date_apdi = DateRangeFilter(field_name="date_apdi", lookup_expr="gte", label="Date APDI entre le")
    end_date_apdi = DateRangeFilter(field_name="date_apdi", lookup_expr="lte", label="et le")
    start_date_apms = DateRangeFilter(field_name="date_apms", lookup_expr="gte", label="Date APMS entre le")
    end_date_apms = DateRangeFilter(field_name="date_apms", lookup_expr="lte", label="et le")
    start_date_levee = DateRangeFilter(
        field_name="date_levee", lookup_expr="gte", label="Date de levée APDI / APMS entre le"
    )
    end_date_levee = DateRangeFilter(field_name="date_levee", lookup_expr="lte", label="et le")

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
            "start_date_confirmation",
            "end_date_confirmation",
            "resultat_confirmation",
            "context_suspicion",
            "start_date_first_symptoms",
            "end_date_first_symptoms",
            "type_detenteur",
            "numero_identifiant_detenteur",
            "commune_detenteur",
            "nom_detenteur",
            "type_lieu",
            "veterinaire",
            "numero_dpe",
            "start_date_apdi",
            "end_date_apdi",
            "start_date_apms",
            "end_date_apms",
            "start_date_levee",
            "end_date_levee",
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

    def filter_date_confirmation(self, queryset, name, value):
        lookup = "gte" if name.startswith("start_") else "lte"
        return queryset.filter(statut_evenement=StatutEvenement.CONFIRME, **{f"date_statut_changed__{lookup}": value})

    def filter_resultat_confirmation(self, queryset, name, value):
        return queryset.filter(pk__in=Analyse.objects.filter(resultat=value).values("evenement"))

    def filter_type_detenteur(self, queryset, name, value):
        queryset = queryset.filter(statut_animal=StatutAnimal.DETENU)
        if value == TypeDetenteur.ETABLISSEMENT:
            return queryset.exclude(numero_identifiant_etablissement="").exclude(
                numero_identifiant_etablissement__isnull=True
            )
        return queryset.exclude(nom_particulier="").exclude(nom_particulier__isnull=True)

    def filter_numero_identifiant_detenteur(self, queryset, name, value):
        value = value.strip()
        return queryset.filter(
            Q(numero_identifiant_etablissement__icontains=value) | Q(siret_etablissement__icontains=value)
        )

    def filter_commune_detenteur(self, queryset, name, value):
        value = value.strip()
        return queryset.filter(
            Q(commune_etablissement__unaccent__icontains=value)
            | Q(code_insee_etablissement__istartswith=value)
            | Q(commune_particulier__unaccent__icontains=value)
            | Q(code_insee_particulier__istartswith=value)
        )

    def filter_nom_detenteur(self, queryset, name, value):
        value = value.strip()
        return queryset.filter(
            Q(raison_sociale_etablissement__unaccent__icontains=value) | Q(nom_particulier__unaccent__icontains=value)
        )

    def filter_veterinaire(self, queryset, name, value):
        value = value.strip()
        veterinaires = Veterinaire.objects.filter(
            Q(nom_structure__unaccent__icontains=value)
            | Q(nom__unaccent__icontains=value)
            | Q(prenom__unaccent__icontains=value)
        )
        return queryset.filter(pk__in=veterinaires.values("evenement"))

    def filter_numero_dpe(self, queryset, name, value):
        veterinaires = Veterinaire.objects.filter(numero_dpe__icontains=value.strip())
        return queryset.filter(pk__in=veterinaires.values("evenement"))

from functools import cached_property

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import CheckboxInput, Media, TextInput
import django_filters
from dsfr.forms import DsfrBaseForm

from core.filters_mixins import (
    WithAgentContactFilterMixin,
    WithDatePublicationFilterMixin,
    WithDateReceptionFilterMixin,
    WithEtatFilterMixin,
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
)
from core.form_mixins import js_module
from core.models import LienLibre
from core.widgets import TreeselectCheckbox, TreeselectGroup
from ssa.constants import CategorieDanger, CategorieProduit
from ssa.filters import WithEtablissementFilterMixin
from tiac.constants import (
    DANGERS_COURANTS,
    SELECTED_HAZARD_CHOICES,
    DangersSyndromiques,
    EvenementFollowUp,
    SuspicionConclusion,
    TypeAliment,
    TypeRepas,
)
from tiac.models import EvenementSimple, InvestigationFollowUp, InvestigationTiac


class TiacFilterForm(DsfrBaseForm):
    fields = "__all__"

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/search_form.mjs"),),
        )

    main_filters = [
        "with_free_links",
        "start_date",
        "end_date",
        "structure_contact",
        "agent_contact",
        "follow_up",
        "suspicion_conclusion",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        simple_choices = [(f"simple-{value}", f"Enr. simple / {label}") for value, label in EvenementFollowUp.choices]
        investigation_choices = [
            (f"tiac-{value}", f"Investigation TIAC / {label}") for value, label in InvestigationFollowUp.choices
        ]
        self.fields["follow_up"].choices = simple_choices + investigation_choices

    @cached_property
    def common_danger(self):
        return DANGERS_COURANTS


class TiacFilter(
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
    follow_up = django_filters.MultipleChoiceFilter(
        label="Type d'événement/suites",
        choices=(
            [(f"simple-{value}", f"Enr. simple / {label}") for value, label in EvenementFollowUp.choices]
            + [(f"tiac-{value}", f"Investigation TIAC / {label}") for value, label in InvestigationFollowUp.choices]
        ),
        method="filter_follow_up",
        widget=TreeselectCheckbox(choices=(), attrs={"placeholder": "Rechercher"}),
    )
    suspicion_conclusion = django_filters.MultipleChoiceFilter(
        label="Conclusion",
        choices=SuspicionConclusion.choices,
        widget=TreeselectCheckbox(choices=(), attrs={"placeholder": "Rechercher"}),
    )
    selected_hazard = django_filters.MultipleChoiceFilter(
        label="Dangers retenus",
        field_name="selected_hazard",
        choices=SELECTED_HAZARD_CHOICES,
        method="filter_selected_hazard",
        widget=TreeselectCheckbox(
            choices=(
                TreeselectGroup(
                    label="Dangers syndromiques",
                    choices=DangersSyndromiques.choices_short_names,
                    can_expand=False,
                    categorised_label=None,
                ),
                TreeselectGroup(
                    label="Liste complète des dangers alimentaires",
                    choices=CategorieDanger.treeselect_groups,
                    can_expand=False,
                    categorised_label=None,
                ),
            )
        ),
    )
    full_text_search = django_filters.CharFilter(
        method="filter_full_text_search",
        label="Recherche libre",
        widget=TextInput(attrs={"placeholder": "Aliment, analyse, repas, établissement..."}),
    )

    etat = django_filters.ChoiceFilter(
        method="filter_etat",
        choices=(*InvestigationTiac.Etat.choices, ("fin de suivi", "Fin de suivi")),
        label="État de l'événement",
        empty_label=settings.SELECT_EMPTY_CHOICE,
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
    numero_sivss = django_filters.CharFilter(
        field_name="numero_sivss",
        lookup_expr="contains",
        distinct=True,
        label="Numéro SIVSS",
        widget=TextInput(
            attrs={"placeholder": "000000", "pattern": r"\d{6}", "maxlength": 6, "title": "6 chiffres requis"}
        ),
    )

    nb_sick_persons = django_filters.ChoiceFilter(
        choices=[
            ("0-5", "[0-5]"),
            ("6-10", "[6-10]"),
            ("11-50", "[11-50]"),
            ("51-+", "[51+]"),
        ],
        label="Nombre de malade total",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_nb_sick_persons",
    )
    nb_dead_persons = django_filters.ChoiceFilter(
        choices=[
            ("0-0", "[0]"),
            ("1-+", "[1+]"),
        ],
        label="Nombre de décédés",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_nb_dead_persons",
    )
    danger_syndromiques_suspectes = django_filters.MultipleChoiceFilter(
        choices=[(c[0], DangersSyndromiques(c[0]).short_name) for c in DangersSyndromiques.choices],
        label="Danger syndromique suspecté",
        method="filter_danger_syndromiques_suspectes",
    )
    agents_pathogenes = django_filters.MultipleChoiceFilter(
        label="Agent pathogène confirmé par l'ARS",
        field_name="agents_confirmes_ars",
        choices=CategorieDanger,
        method="filter_agents_pathogenes",
        widget=TreeselectCheckbox(
            choices=CategorieDanger.treeselect_choices_with_dangers_courants(CategorieDanger.danger_courants_tiac)
        ),
    )
    analyse_categorie_danger = django_filters.MultipleChoiceFilter(
        label="Analyse - Danger détecté",
        field_name="analyses_alimentaires__categorie_danger",
        choices=CategorieDanger,
        method="filter_analyse_categorie_danger",
        widget=TreeselectCheckbox(
            choices=CategorieDanger.treeselect_choices_with_dangers_courants(CategorieDanger.danger_courants_tiac)
        ),
    )
    type_aliment = django_filters.ChoiceFilter(
        choices=TypeAliment,
        label="Aliment - Type d'aliment",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        field_name="aliments__type_aliment",
    )
    aliment_categorie_produit = django_filters.MultipleChoiceFilter(
        label="Aliment - Catégorie de produit",
        field_name="aliments__categorie_produit",
        choices=CategorieProduit,
        method="filter_aliment_categorie_produit",
        widget=TreeselectCheckbox(choices=CategorieProduit.treeselect_groups),
    )
    nb_personnes_repas = django_filters.CharFilter(
        field_name="repas__nombre_participant",
        lookup_expr="contains",
        distinct=True,
        label="Repas - Nombre de participants",
    )
    type_repas = django_filters.ChoiceFilter(
        choices=TypeRepas,
        label="Repas - Type de repas",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        field_name="repas__type_repas",
    )
    numero_resytal = django_filters.CharFilter(
        field_name="etablissements__numero_resytal", lookup_expr="contains", distinct=True, label="Numéro Resytal"
    )

    INVESTIGATION_TIAC_FILTERS = [
        "suspicion_conclusion",
        "numero_sivss",
        "nb_dead_persons",
        "nb_personnes_repas",
        "type_aliment",
        "type_repas",
        "danger_syndromiques_suspectes",
        "aliment_categorie_produit",
        "analyse_categorie_danger",
        "agents_pathogenes",
        "selected_hazard",
    ]

    def _apply_free_links(self, queryset, queryset_type):
        evenement_simple_content_type = ContentType.objects.get_for_model(EvenementSimple)
        investigation_content_type = ContentType.objects.get_for_model(InvestigationTiac)

        if queryset_type == "combined":
            evenement_simple_ids = queryset._querysets[0].values_list("id", flat=True)
            investigation_ids = queryset._querysets[1].values_list("id", flat=True)

            extra_evenement_simple_ids_from_evenement_simple = self._get_related_objects(
                evenement_simple_ids, evenement_simple_content_type, evenement_simple_content_type
            )
            extra_investigation_ids_from_evenement_simple = self._get_related_objects(
                evenement_simple_ids, evenement_simple_content_type, investigation_content_type
            )
            extra_investigation_ids_from_investigation = self._get_related_objects(
                investigation_ids, investigation_content_type, investigation_content_type
            )
            extra_evenement_simple_ids_from_investigations = self._get_related_objects(
                investigation_ids, investigation_content_type, evenement_simple_content_type
            )

            queryset._querysets[0] = self.queryset._querysets[0].filter(
                Q(id__in=evenement_simple_ids)
                | Q(id__in=extra_evenement_simple_ids_from_evenement_simple)
                | Q(id__in=extra_evenement_simple_ids_from_investigations)
            )
            queryset._querysets[1] = self.queryset._querysets[1].filter(
                Q(id__in=investigation_ids)
                | Q(id__in=extra_investigation_ids_from_investigation)
                | Q(id__in=extra_investigation_ids_from_evenement_simple)
            )

        elif queryset_type == "simple":
            evenement_simple_ids = queryset.values_list("id", flat=True)
            qs_1, qs_2 = self._get_related_objects(
                evenement_simple_ids, evenement_simple_content_type, evenement_simple_content_type
            )
            queryset = self.queryset._querysets[0].filter(
                Q(id__in=evenement_simple_ids) | Q(id__in=qs_1) | Q(id__in=qs_2)
            )

        elif queryset_type == "tiac":
            investigation_ids = queryset.values_list("id", flat=True)
            qs_3, qs_4 = self._get_related_objects(
                investigation_ids, investigation_content_type, investigation_content_type
            )
            queryset = self.queryset._querysets[1].filter(Q(id__in=investigation_ids) | Q(id__in=qs_3) | Q(id__in=qs_4))

        return queryset

    def filter_queryset(self, queryset):
        """
        Taken directly from Django filters, but we remove the `assert isinstance` on queryset are we are not using a
        real queryset but a QuerySetSequence instead.
        Adapted so that we filter on the queryset sequence in order to keep only the queryset that has the field we
        want to filter on.
        """
        queryset_type = "combined"
        for filter_name in self.INVESTIGATION_TIAC_FILTERS:
            if self.form.cleaned_data.get(filter_name) not in ("", None, []):
                queryset = self.queryset._querysets[1]
                queryset_type = "tiac"

        fiche_types = set([v.split("-")[0] for v in self.form.cleaned_data["follow_up"]])
        if len(fiche_types) == 1:
            if "simple" in fiche_types:
                if queryset_type == "combined":
                    queryset_type = "simple"
                    queryset = self.queryset._querysets[0]
                elif queryset_type == "tiac":
                    return self.queryset._querysets[0].none()

            if "tiac" in fiche_types:
                if queryset_type == "combined":
                    queryset_type = "simple"
                    queryset = self.queryset._querysets[1]
                elif queryset_type == "simple":
                    return self.queryset._querysets[0].none()

        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)

        if self.form.cleaned_data["full_text_search"]:
            if queryset_type == "combined":
                for i, qs in enumerate(queryset._querysets):
                    queryset._querysets[i] = qs.search(self.form.cleaned_data["full_text_search"])
            else:
                queryset.search(self.form.cleaned_data["full_text_search"])

        if self.form.cleaned_data["with_free_links"] is True:
            queryset = self._apply_free_links(queryset, queryset_type)

        return queryset

    def _get_related_objects(self, ids, obj_content_type, allowed_content_type):
        objects_from_free_links_1 = LienLibre.objects.filter(
            content_type_2=allowed_content_type, content_type_1=obj_content_type, object_id_1__in=ids
        ).values_list("object_id_2", flat=True)
        objects_from_free_links_2 = LienLibre.objects.filter(
            content_type_1=allowed_content_type, content_type_2=obj_content_type, object_id_2__in=ids
        ).values_list("object_id_1", flat=True)
        return list(set(objects_from_free_links_1) | set(objects_from_free_links_2))

    def _range_filter(self, value, field_name, queryset):
        low, high = value.split("-")
        queryset = queryset.filter(**{f"{field_name}__gte": low})
        if high != "+":
            queryset = queryset.filter(**{f"{field_name}__lte": high})
        return queryset

    def filter_nb_sick_persons(self, queryset, name, value):
        return self._range_filter(value, "nb_sick_persons", queryset)

    def filter_nb_dead_persons(self, queryset, name, value):
        return self._range_filter(value, "nb_dead_persons", queryset)

    def filter_danger_syndromiques_suspectes(self, queryset, name, value):
        return queryset.filter(danger_syndromiques_suspectes__contains=value)

    def filter_selected_hazard(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(selected_hazard__overlap=value)

    def filter_agents_pathogenes(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(agents_confirmes_ars__overlap=value)

    def filter_aliment_categorie_produit(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(aliments__categorie_produit__in=value)

    def filter_analyse_categorie_danger(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(analyses_alimentaires__categorie_danger__overlap=value)

    def filter_with_free_links(self, queryset, name, value):
        return queryset

    def filter_follow_up(self, queryset, name, value):
        ids = [v.split("-")[1] for v in value]
        return queryset.filter(follow_up__in=ids)

    def filter_full_text_search(self, queryset, name, value):
        return queryset

    class Meta:
        model = EvenementSimple
        fields = [
            "numero",
            "with_free_links",
            "start_date",
            "end_date",
            "structure_contact",
            "agent_contact",
            "follow_up",
            "suspicion_conclusion",
            "selected_hazard",
            "full_text_search",
            "etat",
        ]
        form = TiacFilterForm

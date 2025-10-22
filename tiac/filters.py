from functools import cached_property

import django_filters
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import DateInput, Media, CheckboxInput, TextInput, HiddenInput
from dsfr.forms import DsfrBaseForm

from core.filters_mixins import WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin
from core.form_mixins import js_module
from core.models import LienLibre
from ssa.filters import WithEtablissementFilterMixin, CharInFilter
from tiac.constants import (
    TypeRepas,
    TypeAliment,
    DangersSyndromiques,
    EvenementFollowUp,
    DANGERS_COURANTS,
    SuspicionConclusion,
)
from tiac.models import EvenementSimple, InvestigationTiac, InvestigationFollowUp


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
    WithStructureContactFilterMixin,
    WithAgentContactFilterMixin,
    WithEtablissementFilterMixin,
    django_filters.FilterSet,
):
    with_free_links = django_filters.BooleanFilter(
        label="Inclure les liaisons", method="filter_with_free_links", widget=CheckboxInput
    )
    start_date = django_filters.DateFilter(
        field_name="date_reception",
        lookup_expr="gte",
        label="Réception entre le",
        widget=DateInput(attrs={"type": "date"}),
    )
    end_date = django_filters.DateFilter(
        field_name="date_reception", lookup_expr="lte", label="et le", widget=DateInput(attrs={"type": "date"})
    )
    follow_up = django_filters.ChoiceFilter(
        label="Type d'événement/suites",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_follow_up",
    )
    suspicion_conclusion = django_filters.ChoiceFilter(
        label="Conclusion",
        choices=SuspicionConclusion.choices,
        empty_label=settings.SELECT_EMPTY_CHOICE,
    )
    selected_hazard = CharInFilter(
        label="Danger retenu",
        field_name="selected_hazard",
        lookup_expr="overlap",
        widget=HiddenInput,
    )
    full_text_search = django_filters.CharFilter(
        method="filter_full_text_search",
        label="Recherche libre",
        widget=TextInput(attrs={"placeholder": "Aliment, analyse, repas, établissement..."}),
    )

    etat = django_filters.ChoiceFilter(
        choices=EvenementSimple.Etat, label="État", empty_label=settings.SELECT_EMPTY_CHOICE
    )
    numero_sivss = django_filters.CharFilter(
        field_name="numero_sivss",
        lookup_expr="contains",
        distinct=True,
        label="Numéro SIVSS",
        widget=TextInput(
            attrs={"placeholder": "000000", "pattern": "\d{6}", "maxlength": 6, "title": "6 chiffres requis"}
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
    agents_pathogenes = CharInFilter(
        label="Agent pathogène confirmé par l'ARS",
        field_name="agents_confirmes_ars",
        lookup_expr="overlap",
        widget=HiddenInput,
    )
    analyse_categorie_danger = CharInFilter(
        label="Analyse - Danger détecté",
        field_name="analyses_alimentaires__categorie_danger",
        lookup_expr="overlap",
        widget=HiddenInput,
    )
    type_aliment = django_filters.ChoiceFilter(
        choices=TypeAliment,
        label="Aliment - Type d'aliment",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        field_name="aliments__type_aliment",
    )
    aliment_categorie_produit = CharInFilter(
        label="Aliment - Catégorie de produit",
        field_name="aliments__categorie_produit",
        lookup_expr="in",
        widget=HiddenInput,
    )
    nb_personnes_repas = django_filters.ChoiceFilter(
        choices=[
            ("0-5", "[0-5]"),
            ("6-10", "[6-10]"),
            ("11-50", "[11-50]"),
            ("51-+", "[51+]"),
        ],
        label="Repas - Nombre de participants",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_nb_personnes_repas",
    )
    type_repas = django_filters.ChoiceFilter(
        choices=TypeRepas,
        label="Repas - Type de repas",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        field_name="repas__type_repas",
    )
    numero_resytal = django_filters.CharFilter(
        field_name="etablissements__numero_resytal", lookup_expr="contains", distinct=True, label="Numéro Résystal"
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
            if self.form.cleaned_data[filter_name] not in ("", None, []):
                queryset = self.queryset._querysets[1]
                queryset_type = "tiac"

        if self.form.cleaned_data["follow_up"].startswith("simple"):
            if queryset_type == "combined":
                queryset_type = "simple"
                queryset = self.queryset._querysets[0]
            elif queryset_type == "tiac":
                return self.queryset._querysets[0].none()

        if self.form.cleaned_data["follow_up"].startswith("tiac"):
            if queryset_type == "combined":
                queryset_type = "tiac"
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

    def filter_nb_personnes_repas(self, queryset, name, value):
        return self._range_filter(value, "repas__nombre_participant", queryset)

    def filter_danger_syndromiques_suspectes(self, queryset, name, value):
        return queryset.filter(danger_syndromiques_suspectes__contains=value)

    def filter_with_free_links(self, queryset, name, value):
        return queryset

    def filter_follow_up(self, queryset, name, value):
        type_fiche, cleaned_value = value.split("-")
        return queryset.filter(follow_up=cleaned_value)

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

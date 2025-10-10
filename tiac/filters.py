import django_filters
from django.conf import settings
from django.forms import DateInput, Media
from dsfr.forms import DsfrBaseForm

from core.filters_mixins import WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin
from core.form_mixins import js_module
from ssa.filters import WithEtablissementFilterMixin
from tiac.constants import TypeRepas, TypeAliment
from tiac.models import EvenementSimple


class TiacFilterForm(DsfrBaseForm):
    fields = "__all__"

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/search_form.mjs"),),
        )

    main_filters = [
        "numero",
        "start_date",
        "end_date",
        "structure_contact",
        "agent_contact",
    ]


class TiacFilter(
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
    WithAgentContactFilterMixin,
    WithEtablissementFilterMixin,
    django_filters.FilterSet,
):
    start_date = django_filters.DateFilter(
        field_name="date_reception",
        lookup_expr="gte",
        label="Réception entre le",
        widget=DateInput(attrs={"type": "date"}),
    )
    end_date = django_filters.DateFilter(
        field_name="date_reception", lookup_expr="lte", label="et le", widget=DateInput(attrs={"type": "date"})
    )

    etat = django_filters.ChoiceFilter(
        choices=EvenementSimple.Etat, label="État", empty_label=settings.SELECT_EMPTY_CHOICE
    )
    numero_sivss = django_filters.CharFilter(
        field_name="numero_sivss", lookup_expr="contains", distinct=True, label="Numéro SIVSS"
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
    type_aliment = django_filters.ChoiceFilter(
        choices=TypeAliment,
        label="Type d'aliment",
        empty_label=settings.SELECT_EMPTY_CHOICE,
        field_name="aliments__type_aliment",
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

    INVESTIGATION_TIAC_FILTERS = ["numero_sivss", "nb_dead_persons", "nb_personnes_repas", "type_aliment", "type_repas"]

    def filter_queryset(self, queryset):
        """
        Taken directly from Django filters, but we remove the `assert isinstance` on queryset are we are not using a
        real queryset but a QuerySetSequence instead.
        Adapted so that we filter on the queryset sequence in order to keep only the queryset that has the field we
        want to filter on.
        """
        for filter_name in self.INVESTIGATION_TIAC_FILTERS:
            if self.form.cleaned_data[filter_name] not in ("", None):
                queryset = self.queryset._querysets[1]

        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)
        return queryset

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

    class Meta:
        model = EvenementSimple
        fields = ["numero", "start_date", "end_date", "structure_contact", "agent_contact", "etat"]
        form = TiacFilterForm

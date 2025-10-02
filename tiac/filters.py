import django_filters
from django.forms import DateInput, Media
from dsfr.forms import DsfrBaseForm

from core.filters_mixins import WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin
from core.form_mixins import js_module
from tiac.models import EvenementSimple


class TiacFilterForm(DsfrBaseForm):
    fields = "__all__"

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/search_form.mjs"),),
        )


class TiacFilter(
    WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin, django_filters.FilterSet
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

    def filter_queryset(self, queryset):
        """
        Taken directly from Django filters, but we remove the `assert isinstance` on queryset are we are not using a
        real queryset but a QuerySetSequence instead
        """
        for name, value in self.form.cleaned_data.items():
            queryset = self.filters[name].filter(queryset, value)
        return queryset

    class Meta:
        model = EvenementSimple
        fields = [
            "numero",
            "start_date",
            "end_date",
            "structure_contact",
            "agent_contact",
        ]
        form = TiacFilterForm

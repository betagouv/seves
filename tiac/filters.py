import django_filters

from core.filters_mixins import WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin
from tiac.models import EvenementSimple


class TiacFilter(
    WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin, django_filters.FilterSet
):
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
        fields = []

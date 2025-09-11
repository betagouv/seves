import django_filters

from core.filters_mixins import WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin
from tiac.models import EvenementSimple


class EvenementSimpleFilter(
    WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin, django_filters.FilterSet
):
    pass

    class Meta:
        model = EvenementSimple
        fields = []

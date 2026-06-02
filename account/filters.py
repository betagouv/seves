from django.conf import settings
from django.contrib.auth import get_user_model
import django_filters
from dsfr.forms import DsfrBaseForm

from core.models import Structure

User = get_user_model()


class AdminUserFilterForm(DsfrBaseForm):
    pass


class AdminUserFilter(django_filters.FilterSet):
    structure_name = django_filters.ModelChoiceFilter(
        label="Structure",
        queryset=Structure.objects.all().order_by("libelle"),
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_structure",
    )

    def filter_structure(self, queryset, name, value):
        return queryset.filter(agent__structure__libelle=value).distinct()

    class Meta:
        model = User
        fields = ["structure_name"]
        form = AdminUserFilterForm

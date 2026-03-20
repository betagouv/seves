from django.db.models import Q
from django.forms.widgets import DateInput
import django_filters

from core.filters_mixins import (
    WithAgentContactFilterMixin,
    WithEtatFilterMixin,
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
)
from core.forms import DSFRForm
from core.models import Region
from seves import settings

from .models import Evenement, OrganismeNuisible


class EvenementFilter(
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
    WithAgentContactFilterMixin,
    WithEtatFilterMixin,
    django_filters.FilterSet,
):
    region = django_filters.ModelChoiceFilter(
        label="Région", queryset=Region.objects.all(), empty_label=settings.SELECT_EMPTY_CHOICE, method="filter_region"
    )
    organisme_nuisible = django_filters.ModelChoiceFilter(
        label="Organisme",
        queryset=OrganismeNuisible.objects.all().order_by("libelle_court"),
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_organisme_nuisible",
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

    class Meta:
        model = Evenement
        fields = [
            "annee",
            "numero",
            "region",
            "organisme_nuisible",
            "start_date",
            "end_date",
            "etat",
        ]
        form = DSFRForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.manual_render_fields = ["structure_contact", "agent_contact"]

    def filter_organisme_nuisible(self, queryset, name, value):
        return queryset.filter(organisme_nuisible__libelle_court__startswith=value).distinct()

    def filter_region(self, queryset, name, value):
        """
        Filtre les événements en fonction d'une région selon deux critères :
        1. Événements ayant au moins une fiche détection avec un ou plusieurs lieux dans la région spécifiée
        2. Événements dont la structure créatrice à un lien à la région spécifiée
        """
        return queryset.filter(
            Q(detections__lieux__departement__region=value) | Q(detections__createur__region=value)
        ).distinct()

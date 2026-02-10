from django.forms.widgets import DateInput
import django_filters

from core.constants import REGION_STRUCTURE_MAPPING
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
        queryset=OrganismeNuisible.objects.all(),
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
        1. Premier niveau : événements ayant au moins une fiche détection avec un ou plusieurs lieux dans la région spécifiée
        2. Deuxième niveau : événements dont la structure créatrice appartient à la région spécifiée (selon un mapping prédéfini) et
         - n'ayant aucun lieu ou,
         - un/plusieurs lieux sans la region renseignée et/ou dans une région différente.
        """
        # Premier niveau
        region_queryset = queryset.filter(detections__lieux__departement__region=value).distinct()
        # Deuxième niveau
        if region_structure := REGION_STRUCTURE_MAPPING.get(value.nom):
            structure_queryset = queryset.filter(detections__createur__niveau2=region_structure).distinct()
            return region_queryset | structure_queryset
        return region_queryset

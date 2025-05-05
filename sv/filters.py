import django_filters
from django.db.models import OuterRef, Exists
from django.forms.widgets import DateInput

from core.form_mixins import DSFRForm
from core.filters_mixins import WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin
from seves import settings
from .models import FicheDetection, Region, OrganismeNuisible, Evenement


class EvenementFilter(
    WithNumeroFilterMixin, WithStructureContactFilterMixin, WithAgentContactFilterMixin, django_filters.FilterSet
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
    etat = django_filters.ChoiceFilter(choices=Evenement.Etat, label="État", empty_label=settings.SELECT_EMPTY_CHOICE)

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
        # Recherche des événements qui ont au moins une fiche de détection avec un lieu dans cette région
        fiches_in_region = FicheDetection.objects.filter(evenement=OuterRef("pk"), lieux__departement__region=value)
        return queryset.filter(Exists(fiches_in_region)).distinct()

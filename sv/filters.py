from functools import reduce
from operator import or_

from django.db.models import Q
import django_filters

from core.filters_mixins import (
    WithAgentContactFilterMixin,
    WithDatePublicationFilterMixin,
    WithEtatFilterMixin,
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
)
from core.forms import DSFRForm
from core.models import Region
from core.widgets import TreeselectCheckbox

from .models import Evenement, OrganismeNuisible


class EvenementFilter(
    WithNumeroFilterMixin,
    WithStructureContactFilterMixin,
    WithAgentContactFilterMixin,
    WithEtatFilterMixin,
    WithDatePublicationFilterMixin,
    django_filters.FilterSet,
):
    region = django_filters.ModelMultipleChoiceFilter(
        label="Région",
        queryset=Region.objects.all(),
        method="filter_region",
        widget=TreeselectCheckbox(
            choices=(),
            attrs={"placeholder": "Rechercher"},
        ),
    )
    organisme_nuisible = django_filters.ModelMultipleChoiceFilter(
        label="Organisme",
        queryset=OrganismeNuisible.objects.all().order_by("libelle_court"),
        method="filter_organisme_nuisible",
        widget=TreeselectCheckbox(
            choices=(),
            attrs={"placeholder": "Rechercher"},
        ),
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
        return queryset.filter(
            reduce(
                or_,
                (Q(organisme_nuisible__libelle_court__startswith=v) for v in value),
                Q(),
            )
        ).distinct()

    def filter_region(self, queryset, name, value):
        """
        Filtre les événements en fonction d'une région selon deux critères :
        1. Événements ayant au moins une fiche détection avec un ou plusieurs lieux dans la région spécifiée
        2. Événements dont la structure créatrice à un lien à la région spécifiée
        """
        if not value:
            return queryset
        return queryset.filter(
            Q(detections__lieux__departement__region__in=value) | Q(detections__createur__region__in=value)
        ).distinct()

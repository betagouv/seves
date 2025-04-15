import re

import django_filters
from django.db.models import OuterRef, Exists

from core.form_mixins import DSFRForm
from seves import settings
from .models import FicheDetection, Region, OrganismeNuisible, Evenement
from django.forms.widgets import DateInput, TextInput


class EvenementFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(
        method="filter_numero",
        label="Numéro évènement",
        widget=TextInput(
            attrs={
                "placeholder": "2024",
                "pattern": "^\\d{4}(\\.\\d+)?$",
                "title": "Le format attendu est AAAA ou AAAA.N (ex: 2025 ou 2024.5)",
            }
        ),
    )
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
        self._validate_numero_format()

    def _validate_numero_format(self):
        numero = self.data.get("numero")
        if not numero:
            return
        errors = self.errors.get("numero", [])

        if not re.match(r"^\d{4}(\.\d+)?$", numero):
            errors.append("Format 'numero' invalide. Le format attendu est AAAA ou AAAA.N (ex: 2025 ou 2025.1)")
            return

        try:
            _annee = int(numero[:4])
        except ValueError:
            errors.append("Format 'numero' invalide. Le numéro doit commencer par quatre chiffres'")

        self.errors["numero"] = errors

    def filter_numero(self, queryset, name, value):
        if self.errors.get("numero") or not value:
            return queryset

        parts = value.split(".")
        if len(parts) == 1:
            return queryset.filter(numero_annee=int(parts[0]))
        if len(parts) == 2:
            return queryset.filter(numero_annee=int(parts[0]), numero_evenement=int(parts[1]))
        return queryset

    def filter_organisme_nuisible(self, queryset, name, value):
        return queryset.filter(organisme_nuisible__libelle_court__startswith=value).distinct()

    def filter_region(self, queryset, name, value):
        # Recherche des événements qui ont au moins une fiche de détection avec un lieu dans cette région
        fiches_in_region = FicheDetection.objects.filter(evenement=OuterRef("pk"), lieux__departement__region=value)
        return queryset.filter(Exists(fiches_in_region)).distinct()

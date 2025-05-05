import re

import django_filters
from django.forms.widgets import TextInput

from core.models import Contact, Structure
from seves import settings


class WithNumeroFilterMixin(django_filters.FilterSet):
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


class WithStructureContactFilterMixin(django_filters.FilterSet):
    structure_contact = django_filters.ModelChoiceFilter(
        label="Structure en contact",
        queryset=(
            Contact.objects.structures_only()
            .filter(structure__in=Structure.objects.can_be_contacted())
            .order_by("structure__libelle")
            .select_related("structure")
        ),
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_structure_contact",
    )

    def filter_structure_contact(self, queryset, name, value):
        return queryset.filter(contacts=value)


class WithAgentContactFilterMixin(django_filters.FilterSet):
    agent_contact = django_filters.ModelChoiceFilter(
        label="Agent en contact",
        queryset=(
            Contact.objects.agents_only()
            .can_be_emailed()
            .select_related("agent", "agent__structure")
            .order_by_structure_and_name()
        ),
        empty_label=settings.SELECT_EMPTY_CHOICE,
        method="filter_agent_contact",
    )

    def filter_agent_contact(self, queryset, name, value):
        return queryset.filter(contacts=value)

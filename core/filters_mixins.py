from django.db.models import Q
from django.forms.widgets import TextInput
import django_filters

from core.mixins import WithEtatMixin
from core.models import Contact, Structure
from seves import settings


class WithNumeroFilterMixin(django_filters.FilterSet):
    numero = django_filters.CharFilter(
        method="filter_numero",
        label="Numéro évènement",
        widget=TextInput(
            attrs={
                "placeholder": "2024",
            }
        ),
    )

    def filter_numero(self, queryset, name, value):
        if self.errors.get("numero") or not value:
            return queryset

        parts = value.split(".")
        if len(parts) == 1:
            return queryset.filter(Q(numero_annee__icontains=parts[0]) | Q(numero_evenement__icontains=parts[0]))
        if len(parts) == 2:
            return queryset.filter(numero_annee__icontains=parts[0], numero_evenement__icontains=parts[1])
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


class WithEtatFilterMixin(django_filters.FilterSet):
    etat = django_filters.ChoiceFilter(
        method="filter_etat",
        choices=tuple(WithEtatMixin.Etat.choices) + (("fin de suivi", "Fin de suivi"),),
        label="État de l'événement",
        empty_label=settings.SELECT_EMPTY_CHOICE,
    )

    def filter_etat(self, queryset, name, value):
        if value == "fin de suivi":
            return queryset.filter(has_fin_de_suivi=True)
        return queryset.filter(etat=value, has_fin_de_suivi=False)

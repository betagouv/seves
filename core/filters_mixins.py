from django.forms import DateInput
from django.forms.widgets import TextInput
import django_filters

from core.mixins import WithEtatMixin
from core.models import Contact, Structure
from seves import settings


class WithNumeroFilterMixin(django_filters.FilterSet):
    annee = django_filters.CharFilter(
        method="filter_annee",
        label="Année",
        widget=TextInput(
            attrs={
                "placeholder": "AAAA",
            }
        ),
    )
    numero = django_filters.CharFilter(
        method="filter_numero",
        label="N° événement",
        widget=TextInput(
            attrs={
                "placeholder": "XXXXX",
            }
        ),
    )

    def filter_annee(self, queryset, name, value):
        if self.errors.get("annee") or not value:
            return queryset

        return queryset.filter(numero_annee=value)

    def filter_numero(self, queryset, name, value):
        if self.errors.get("numero") or not value:
            return queryset
        return queryset.filter(numero_evenement=value.lstrip("0"))


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


class WithDatePublicationFilterMixin(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name="date_publication__date",
        lookup_expr="gte",
        label="Publication entre le",
        widget=DateInput(attrs={"type": "date"}),
    )
    end_date = django_filters.DateFilter(
        field_name="date_publication__date", lookup_expr="lte", label="et le", widget=DateInput(attrs={"type": "date"})
    )


class WithDateReceptionFilterMixin(django_filters.FilterSet):
    start_date_reception = django_filters.DateFilter(
        field_name="date_reception",
        lookup_expr="gte",
        label="Réception entre le",
        widget=DateInput(attrs={"type": "date"}),
    )
    end_date_reception = django_filters.DateFilter(
        field_name="date_reception", lookup_expr="lte", label="et le", widget=DateInput(attrs={"type": "date"})
    )

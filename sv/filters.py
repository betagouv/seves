import django_filters

from core.fields import DSFRRadioButton
from core.forms import DSFRForm
from seves import settings
from .models import FicheDetection, Region, OrganismeNuisible, Evenement
from django.forms.widgets import DateInput, TextInput


class FicheFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(
        method="filter_numero",
        label="Numéro",
        widget=TextInput(attrs={"pattern": "^[0-9]{4}\\.[0-9]+$", "title": "Format attendu : ANNEE.NUMERO"}),
    )
    type_fiche = django_filters.ChoiceFilter(
        choices=[("detection", "Détection"), ("zone", "Zone")],
        label="Type",
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        empty_label=None,
        initial="Détection",
    )
    lieux__departement__region = django_filters.ModelChoiceFilter(
        label="Région", queryset=Region.objects.all(), empty_label=settings.SELECT_EMPTY_CHOICE, method="filter_region"
    )
    evenement__organisme_nuisible = django_filters.ModelChoiceFilter(
        label="Organisme", queryset=OrganismeNuisible.objects.all(), empty_label=settings.SELECT_EMPTY_CHOICE
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
    evenement__etat = django_filters.ChoiceFilter(
        choices=Evenement.Etat, label="État", empty_label=settings.SELECT_EMPTY_CHOICE
    )

    class Meta:
        model = FicheDetection
        fields = [
            "numero",
            "type_fiche",
            "lieux__departement__region",
            "evenement__organisme_nuisible",
            "start_date",
            "end_date",
            "evenement__etat",
        ]
        form = DSFRForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get("numero"):
            try:
                _annee, _numero = map(int, self.data.get("numero").split("."))
            except ValueError:
                errors = self.errors.get("numero", [])
                errors.append("Format 'numero' invalide. Il devrait être 'annee.numero'")
                self.errors["numero"] = errors

    def filter_queryset(self, queryset):
        self.form.cleaned_data.pop("type_fiche")
        return super().filter_queryset(queryset)

    def filter_numero(self, queryset, name, value):
        if self.errors.get("numero") or not value:
            return queryset
        annee, numero = map(int, value.split("."))
        return queryset.filter(numero__annee=annee, numero__numero=numero)

    def filter_region(self, queryset, name, value):
        return queryset.filter(lieux__departement__region=value).distinct()

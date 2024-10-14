import django_filters

from core.forms import DSFRForm
from .models import FicheDetection, Region, OrganismeNuisible, Etat
from django.forms.widgets import DateInput, TextInput


class FicheDetectionFilter(django_filters.FilterSet):
    numero_input = TextInput(attrs={"pattern": "^[0-9]{4}\\.[0-9]+$", "title": "Format attendu : ANNEE.NUMERO"})
    numero = django_filters.CharFilter(method="filter_numero", label="Numéro", widget=numero_input)
    lieux__departement__region = django_filters.ModelChoiceFilter(label="Région", queryset=Region.objects.all())
    organisme_nuisible = django_filters.ModelChoiceFilter(label="Organisme", queryset=OrganismeNuisible.objects.all())
    start_date = django_filters.DateFilter(
        field_name="date_creation__date",
        lookup_expr="gte",
        label="Période du",
        widget=DateInput(attrs={"type": "date"}),
    )
    end_date = django_filters.DateFilter(
        field_name="date_creation__date", lookup_expr="lte", label="Au", widget=DateInput(attrs={"type": "date"})
    )
    etat = django_filters.ModelChoiceFilter(label="État", queryset=Etat.objects.all())

    class Meta:
        model = FicheDetection
        fields = ["numero", "lieux__departement__region", "organisme_nuisible", "start_date", "end_date", "etat"]
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

    def filter_numero(self, queryset, name, value):
        if self.errors.get("numero") or not value:
            return queryset
        annee, numero = map(int, value.split("."))
        return queryset.filter(numero__annee=annee, numero__numero=numero)

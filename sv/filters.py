import django_filters
from django.db.models import TextChoices
from django.forms import forms

from core.fields import DSFRRadioButton
from core.forms import DSFRForm
from seves import settings
from .models import FicheDetection, Region, OrganismeNuisible, Evenement
from django.forms.widgets import DateInput


class TypeFiche(TextChoices):
    DETECTION = ("detection", "Détection")
    ZONE = ("zone", "Zone")


class FicheFilterForm(DSFRForm, forms.Form):
    manual_render_fields = ["type_fiche"]


class FicheFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(method="filter_numero", label="Numéro")
    type_fiche = django_filters.ChoiceFilter(
        choices=TypeFiche.choices,
        label="Type",
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        empty_label=None,
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
        form = FicheFilterForm

    @property
    def _is_detection(self):
        return self.data.get("type_fiche") == TypeFiche.DETECTION

    @property
    def _is_zone(self):
        return self.data.get("type_fiche") == TypeFiche.ZONE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get("type_fiche"):
            data = self.data.copy()
            data["type_fiche"] = TypeFiche.DETECTION
            self.data = data
        self.form.fields["numero"].widget.attrs.update(self._get_numero_validation_attrs(self.data.get("type_fiche")))
        self._validate_numero_format()

    def _validate_numero_format(self):
        if not self.data.get("numero"):
            return

        try:
            list_of_numero = [int(numero) for numero in self.data.get("numero").split(".")]
            assert len(list_of_numero) == 3 if self._is_detection else 2
        except (ValueError, AssertionError):
            errors = self.errors.get("numero", [])
            format_type = "annee.numero.numero" if self._is_detection else "annee.numero"
            errors.append(f"Format 'numero' invalide. Le format correct est '{format_type}'")
            self.errors["numero"] = errors

    def _get_numero_validation_attrs(self, type_fiche):
        if self._is_detection:
            return {"pattern": "^[0-9]{4}\\.[0-9]+\\.[0-9]+$", "title": "Format attendu : ANNEE.NUMERO.NUMERO"}
        if self._is_zone:
            return {"pattern": "^[0-9]{4}\\.[0-9]+$", "title": "Format attendu : ANNEE.NUMERO"}

    def filter_queryset(self, queryset):
        self.form.cleaned_data.pop("type_fiche")
        return super().filter_queryset(queryset)

    def filter_numero(self, queryset, name, value):
        if self.errors.get("numero") or not value:
            return queryset

        if self._is_detection:
            return queryset.filter(numero_detection=value)
        if self._is_zone:
            parts = list(map(int, value.split(".")))
            return queryset.filter(evenement__numero_annee=parts[0], evenement__numero_evenement=parts[1])

    def filter_region(self, queryset, name, value):
        return queryset.filter(lieux__departement__region=value).distinct()

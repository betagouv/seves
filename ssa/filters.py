import django_filters
from django.forms import DateInput, TextInput

from core.filters_mixins import WithNumeroFilterMixin
from core.forms import DSFRForm
from ssa.models import EvenementProduit


class EvenementProduitFilter(WithNumeroFilterMixin, django_filters.FilterSet):
    numero_rasff = django_filters.CharFilter(
        label="Numéro RASFF/AAC",
        widget=TextInput(
            attrs={
                "placeholder": "0000.0000 ou 000000",
                "pattern": "^(\d{4}\.\d{4}|AA\d{2}\.\d{4}|\d{6})$",
                "title": "Le format attendu est XXXX.YYYY ou AAXX.YYYY ou XXXXXX (ex: 2025.1234 ou AA24.1234 ou 123456)",
            }
        ),
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
        model = EvenementProduit
        fields = [
            "numero",
            "numero_rasff",
            "start_date",
            "end_date",
            "type_evenement",
        ]
        form = DSFRForm

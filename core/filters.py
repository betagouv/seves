import django_filters
from django.forms import forms, TextInput
from dsfr.forms import DsfrBaseForm

from .models import Document, Structure
from .form_mixins import DSFRForm


class FilterForm(DSFRForm, forms.Form):
    pass


class DSFRFilterForm(DsfrBaseForm, forms.Form):
    pass


class DocumentFilter(django_filters.FilterSet):
    document_type = django_filters.ChoiceFilter(
        choices=[],
        label="Type de Document",
    )
    created_by_structure = django_filters.ModelChoiceFilter(
        queryset=Structure.objects.none(),
        field_name="created_by_structure",
        label="Ajouté par",
    )

    class Meta:
        model = Document
        fields = ["document_type", "created_by_structure"]
        form = FilterForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        actual_document_types = (
            self.queryset.values_list("document_type", flat=True).order_by("document_type").distinct("document_type")
        )
        self.filters["document_type"].extra["choices"] = [
            (k, v) for (k, v) in Document.TypeDocument.choices if k in actual_document_types
        ]

        ids = self.queryset.values_list("created_by_structure", flat=True).distinct()
        structure_queryset = Structure.objects.filter(id__in=ids).order_by("libelle")
        self.filters["created_by_structure"].queryset = structure_queryset


class MessageFilter(django_filters.FilterSet):
    full_text_search = django_filters.CharFilter(
        method="filter_full_text_search",
        label="",
        widget=TextInput(attrs={"placeholder": "Tapez un terme pour chercher dans les messages"}),
    )

    class Meta:
        model = Document
        fields = ["full_text_search"]
        form = DSFRFilterForm

    def filter_full_text_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.search(value)

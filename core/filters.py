import django_filters
from django.forms import forms

from .models import Document, Structure
from .form_mixins import DSFRForm


class FilterForm(DSFRForm, forms.Form):
    pass


class DocumentFilter(django_filters.FilterSet):
    document_type = django_filters.ChoiceFilter(
        choices=[],
        label="Type de Document",
    )
    created_by_structure = django_filters.ModelChoiceFilter(
        queryset=Structure.objects.all(),
        field_name="created_by_structure",
        label="Structure",
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

        structure_queryset = Structure.objects.filter(
            id__in=self.queryset.values_list("created_by_structure", flat=True).distinct()
        )
        self.filters["created_by_structure"].queryset = structure_queryset

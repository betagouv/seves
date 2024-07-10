import django_filters
from django.forms import forms

from .models import Document
from .forms import DSFRForm


class FilterForm(DSFRForm, forms.Form):
    pass


class DocumentFilter(django_filters.FilterSet):
    class Meta:
        model = Document
        fields = [
            "document_type",
        ]
        form = FilterForm

from django import forms
from dsfr.forms import DsfrBaseForm

from core.widgets import NumericTextInput, TreeselectRadio
from sa.models import Espece
from sa.models.especes_concernees import EspeceConcernee


class EspeceConcerneeForm(DsfrBaseForm, forms.ModelForm):
    espece = forms.ModelChoiceField(
        queryset=Espece.objects.all(),
        required=True,
        widget=TreeselectRadio(
            choices=Espece.all_treeselect_choices, attrs={"placeholder": "Rechercher", "required": True}
        ),
        label="Espèce",
    )

    class Meta:
        model = EspeceConcernee
        fields = [
            "espece",
            "identifiant",
            "presents",
            "morts",
            "cas",
            "abattus",
            "depeuples",
            "vaccines",
        ]
        widgets = {
            "presents": NumericTextInput,
            "morts": NumericTextInput,
            "cas": NumericTextInput,
            "abattus": NumericTextInput,
            "depeuples": NumericTextInput,
            "vaccines": NumericTextInput,
        }

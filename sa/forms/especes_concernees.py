from django import forms
from dsfr.forms import DsfrBaseForm

from core.widgets import NumericTextInput
from sa.models import Espece
from sa.models.especes_concernees import EspeceConcernee


class EspeceConcerneeForm(DsfrBaseForm, forms.ModelForm):
    espece = forms.ModelChoiceField(queryset=Espece.objects.all(), empty_label="Choisir l'espèce")

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

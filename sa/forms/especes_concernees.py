from django import forms
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField
from core.widgets import NumericTextInput, TreeselectRadio
from sa.models import Espece
from sa.models.especes_concernees import EspeceConcernee
from sa.referentiels import situation_unite


class EspeceConcerneeForm(DsfrBaseForm, forms.ModelForm):
    espece = forms.ModelChoiceField(
        queryset=Espece.objects.all(),
        required=True,
        widget=TreeselectRadio(
            choices=Espece.all_treeselect_choices, attrs={"placeholder": "Rechercher", "required": True}
        ),
        label="Espèce",
    )

    type_lieu = SEVESChoiceField(required=False, label="Type de lieu")
    mode_elevage = SEVESChoiceField(required=False, label="Mode d'élevage")
    type_production = SEVESChoiceField(required=False, label="Type de production")
    type_elevage = SEVESChoiceField(required=False, label="Type d'élevage")

    def __init__(self, *args, situation_unite_rows=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = situation_unite.choices_by_level(situation_unite_rows)
        empty_choice = self.fields["type_lieu"].choices[:1]
        self.fields["type_lieu"].choices = empty_choice + choices["type_lieu"]
        self.fields["mode_elevage"].choices = empty_choice + choices["mode_elevage"]
        self.fields["type_production"].choices = empty_choice + choices["type_production"]
        self.fields["type_elevage"].choices = empty_choice + choices["type_elevage"]

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
            "type_lieu",
            "mode_elevage",
            "type_production",
            "type_elevage",
        ]
        widgets = {
            "presents": NumericTextInput,
            "morts": NumericTextInput,
            "cas": NumericTextInput,
            "abattus": NumericTextInput,
            "depeuples": NumericTextInput,
            "vaccines": NumericTextInput,
        }

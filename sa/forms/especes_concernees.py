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
        if not self.is_bound:
            self.initial.setdefault("type_lieu", self.instance.type_lieu)
            self.initial.setdefault("mode_elevage", self.instance.mode_elevage)
            self.initial.setdefault("type_production", self.instance.type_production)
            self.initial.setdefault("type_elevage", self.instance.type_elevage)

    def clean(self):
        cleaned_data = super().clean()
        type_lieu = cleaned_data.get("type_lieu") or ""
        mode_elevage = cleaned_data.get("mode_elevage") or ""
        type_production = cleaned_data.get("type_production") or ""
        type_elevage = cleaned_data.get("type_elevage") or ""

        if not any((type_lieu, mode_elevage, type_production, type_elevage)):
            self.instance.situation_unite_regle = None
            return cleaned_data

        espece = cleaned_data.get("espece")
        regle = None
        if espece is not None:
            regle = espece.situation_unite_regles.filter(
                type_lieu=type_lieu,
                mode_elevage=mode_elevage,
                type_production=type_production,
                type_elevage=type_elevage,
            ).first()

        if regle is None:
            self.add_error(
                "type_lieu", "La situation renseignée ne correspond pas aux valeurs possibles pour cette espèce."
            )
        else:
            self.instance.situation_unite_regle = regle

        return cleaned_data

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

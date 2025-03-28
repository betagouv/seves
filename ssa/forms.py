from django import forms

from core.fields import SEVESChoiceField, DSFRRadioButton
from core.forms import DSFRForm
from ssa.models import EvenementProduit, TypeEvenement, Source, CerfaRecu, TemperatureConservation, ActionEngagees
from ssa.models.evenement_produit import PretAManger


class EvenementProduitForm(DSFRForm, forms.ModelForm):
    type_evenement = SEVESChoiceField(choices=TypeEvenement.choices, label="Type d'événement")
    numero_rasff = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"pattern": "^(\d{4}\.\d{4}|AA\d{2}\.\d{4})$", "placeholder": "0000.0000"}),
        label="N° RASFF/ACC",
    )
    source = SEVESChoiceField(choices=Source.choices, required=False)
    cerfa_recu = SEVESChoiceField(choices=CerfaRecu.choices, required=False)

    lots = forms.CharField(required=False, widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Lots, DLC/DDM")
    description_complementaire = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "cols": 30,
                "rows": 4,
                "placeholder": "Conditionnement, quantité, mentions d'étiquetage, importateur...",
            }
        ),
        label="Description complémentaire",
    )
    temperature_conservation = forms.ChoiceField(
        required=False,
        choices=TemperatureConservation.choices,
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        label="Température de conservation",
    )
    produit_pret_a_manger = forms.ChoiceField(
        required=False,
        choices=PretAManger.choices,
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        label="Produit Prêt à manger (PAM)",
    )

    actions_engagees = forms.ChoiceField(
        required=False,
        choices=ActionEngagees.choices,
        help_text="En cas de multiples mesures, indiquer la plus contraigrante ou la dernière en date",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_rasff")

    class Meta:
        model = EvenementProduit
        exclude = ["createur", "numero_annee", "numero_evenement", "etat"]

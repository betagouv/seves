from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from core.fields import SEVESChoiceField, DSFRRadioButton
from core.forms import DSFRForm
from ssa.fields import SelectWithAttributeField
from ssa.models import (
    EvenementProduit,
    TypeEvenement,
    Source,
    CerfaRecu,
    TemperatureConservation,
    ActionEngagees,
    Etablissement,
    TypeExploitant,
    PositionDossier,
)
from ssa.models.evenement_produit import PretAManger
from ssa.widgets import PositionDossierWidget


class EvenementProduitForm(DSFRForm, forms.ModelForm):
    type_evenement = SEVESChoiceField(choices=TypeEvenement.choices, label="Type d'événement")
    numero_rasff = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"pattern": "^(\d{4}\.\d{4}|AA\d{2}\.\d{4})$", "placeholder": "0000.0000"}),
        label="N° RASFF/ACC",
    )
    source = SEVESChoiceField(choices=Source.choices, required=False, widget=SelectWithAttributeField)
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

    numeros_rappel_conso = SimpleArrayField(base_field=forms.CharField(), required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_rasff")

    class Meta:
        model = EvenementProduit
        exclude = ["createur", "numero_annee", "numero_evenement", "etat"]


class EtablissementForm(DSFRForm, forms.ModelForm):
    siret = forms.CharField(
        required=False,
        max_length=14,
        label="N° SIRET",
        widget=forms.TextInput(
            attrs={
                "pattern": "[0-9]{14}",
                "placeholder": "110 070 018 00012",
                "title": "Le Siret doit contenir exactement 14 chiffres",
            }
        ),
    )
    code_insee = forms.CharField(widget=forms.HiddenInput(), required=False)
    type_exploitant = SEVESChoiceField(choices=TypeExploitant.choices, label="Type d'exploitant", required=False)
    position_dossier = SEVESChoiceField(
        choices=PositionDossier.choices, label="Position dossier", required=False, widget=PositionDossierWidget
    )

    class Meta:
        model = Etablissement
        exclude = []

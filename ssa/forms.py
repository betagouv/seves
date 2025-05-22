from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django_countries.fields import CountryField

from core.fields import SEVESChoiceField, DSFRRadioButton, ContactModelMultipleChoiceField
from core.form_mixins import DSFRForm
from core.forms import BaseMessageForm
from core.mixins import WithEtatMixin
from core.models import Contact, Message
from ssa.fields import SelectWithAttributeField
from ssa.form_mixins import WithEvenementProduitFreeLinksMixin
from ssa.models import Etablissement, TypeExploitant, PositionDossier, CategorieDanger
from ssa.models import EvenementProduit, TypeEvenement, Source, TemperatureConservation, ActionEngagees
from ssa.models.evenement_produit import PretAManger, QuantificationUnite, CategorieProduit
from ssa.widgets import PositionDossierWidget


class EvenementProduitForm(DSFRForm, WithEvenementProduitFreeLinksMixin, forms.ModelForm):
    type_evenement = SEVESChoiceField(choices=TypeEvenement.choices, label="Type d'événement")
    numero_rasff = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"pattern": "^(\d{4}\.\d{4}|AA\d{2}\.\d{4}|\d{6})$", "placeholder": "0000.0000 ou 000000"}
        ),
        label="N° RASFF/AAC",
    )
    source = SEVESChoiceField(choices=Source.choices, required=False, widget=SelectWithAttributeField)

    categorie_produit = SEVESChoiceField(required=False, choices=CategorieProduit.choices, widget=forms.HiddenInput)
    lots = forms.CharField(required=False, widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Lots, DLC/DDM")
    description_complementaire = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "cols": 30,
                "rows": 4,
                "placeholder": "Conditionnement, quantité, mentions d'étiquetage...",
            }
        ),
        label="Description complémentaire",
    )

    categorie_danger = SEVESChoiceField(required=False, choices=CategorieDanger.choices, widget=forms.HiddenInput)
    quantification_unite = SEVESChoiceField(
        required=False,
        choices=QuantificationUnite.with_opt_group(),
        label="Unité",
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

    actions_engagees = SEVESChoiceField(
        required=False,
        choices=ActionEngagees.choices,
        help_text="En cas de multiples mesures, indiquer la plus contraigrante ou la dernière en date",
    )

    numeros_rappel_conso = SimpleArrayField(base_field=forms.CharField(), required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._add_free_links(model=EvenementProduit)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_rasff")

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS
        self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance

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
    adresse_lieu_dit = forms.CharField(widget=forms.Select(), required=False)
    pays = CountryField(blank=True).formfield()
    type_exploitant = SEVESChoiceField(choices=TypeExploitant.choices, label="Type d'exploitant", required=False)
    position_dossier = SEVESChoiceField(
        choices=PositionDossier.choices, label="Position dossier", required=False, widget=PositionDossierWidget
    )

    class Meta:
        model = Etablissement
        exclude = []


class MessageForm(BaseMessageForm):
    recipients_limited_recipients = ContactModelMultipleChoiceField(
        queryset=Contact.objects.get_ssa_structures(), label="Destinataires", required=False
    )
    manual_render_fields = [
        "recipients_structures_only",
        "recipients_copy_structures_only",
        "recipients_limited_recipients",
    ]

    class Meta(BaseMessageForm.Meta):
        fields = [
            "recipients",
            "recipients_structures_only",
            "recipients_copy",
            "recipients_copy_structures_only",
            "recipients_limited_recipients",
            "message_type",
            "title",
            "content",
            "content_type",
            "object_id",
            "status",
        ]

    def clean(self):
        super().clean()
        if self.cleaned_data["message_type"] in Message.TYPES_WITH_LIMITED_RECIPIENTS:
            self.cleaned_data["recipients"] = self.cleaned_data["recipients_limited_recipients"]

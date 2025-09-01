from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from core.fields import SEVESChoiceField, DSFRRadioButton, ContactModelMultipleChoiceField
from core.form_mixins import DSFRForm
from core.forms import BaseMessageForm, BaseEtablissementForm
from core.mixins import WithEtatMixin
from core.models import Contact, Message
from ssa.form_mixins import WithEvenementProduitFreeLinksMixin
from ssa.models import Etablissement, PositionDossier, CategorieDanger
from ssa.models import EvenementProduit, TypeEvenement, Source, TemperatureConservation, ActionEngagees
from ssa.models.evenement_produit import PretAManger, QuantificationUnite, CategorieProduit
from ssa.widgets import PositionDossierWidget


class EvenementProduitForm(DSFRForm, WithEvenementProduitFreeLinksMixin, forms.ModelForm):
    type_evenement = SEVESChoiceField(choices=TypeEvenement.choices, label="Type d'événement")
    numero_rasff = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"pattern": r"^(\d{4}\.\d{4}|AA\d{2}\.\d{4}|\d{6})$", "placeholder": "0000.0000 ou 000000"}
        ),
        label="N° RASFF/AAC",
    )
    source = SEVESChoiceField(choices=Source.choices, required=False)

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
    precision_danger = forms.CharField(
        required=False,
        label="Précision danger",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Sérotype, molécule...",
            }
        ),
    )
    quantification = forms.CharField(
        required=False,
        label="Résultat analytique du danger",
        widget=forms.CharField.widget(attrs={"placeholder": "détecté / non détecté, quantification"}),
    )
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

    def clean(self):
        super().clean()
        if self.cleaned_data["categorie_danger"] not in CategorieDanger.dangers_bacteriens():
            self.cleaned_data["produit_pret_a_manger"] = ""

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS

        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance

    class Meta:
        model = EvenementProduit
        exclude = ["createur", "numero_annee", "numero_evenement", "etat"]
        widgets = {
            "evaluation": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Préciser si besoin (facultatif) : analyse du danger et du risque par le professionnel, "
                        "par les autorités, évaluation de la situation"
                    )
                },
            )
        }


class EtablissementForm(DSFRForm, BaseEtablissementForm, forms.ModelForm):
    numero_agrement = forms.CharField(
        required=False,
        label="Numéro d'agrément",
        widget=forms.TextInput(attrs={"pattern": r"^\d{2,3}\.\d{2,3}\.\d{2,3}$", "placeholder": "00(0).00(0).00(0)"}),
    )
    type_exploitant = forms.CharField(
        label="Type d'exploitant",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Siège/usine, producteur/affineur, importateur/distributeur…", "maxlength": 45}
        ),
    )
    position_dossier = SEVESChoiceField(
        choices=PositionDossier.choices,
        label="Position dossier",
        required=False,
        widget=PositionDossierWidget(attrs={"class": "fr-select"}),
    )

    manual_render_fields = ["DELETE", "position_dossier", "type_exploitant"]

    class Meta:
        model = Etablissement
        fields = [
            "siret",
            "numero_agrement",
            "raison_sociale",
            "enseigne_usuelle",
            "adresse_lieu_dit",
            "commune",
            "code_insee",
            "departement",
            "pays",
            "type_exploitant",
            "position_dossier",
            "numeros_resytal",
        ]


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

    def __init__(self, *args, **kwargs):
        kwargs["limit_contacts_to"] = "ssa"
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.cleaned_data["message_type"] in Message.TYPES_WITH_LIMITED_RECIPIENTS:
            self.cleaned_data["recipients"] = self.cleaned_data["recipients_limited_recipients"]

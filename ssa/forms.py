import json

from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.forms import Media
from django.utils import timezone
from django.utils.safestring import mark_safe
from dsfr.forms import DsfrBaseForm

from core.fields import ContactModelMultipleChoiceField, DSFRRadioButton, SEVESChoiceField
from core.form_mixins import DSFRForm, js_module
from core.forms import BaseCompteRenduDemandeInterventionForm, BaseEtablissementForm, BaseMessageForm
from core.mixins import WithEtatMixin, WithCommonContextVars
from core.models import Contact, Message
from ssa.constants import (
    CategorieDanger,
    CategorieProduit,
    Source,
    TypeEvenement,
    SourceInvestigationCasHumain,
    PretAManger,
)
from ssa.form_mixins import WithEvenementProduitFreeLinksMixin
from ssa.models import (
    ActionEngagees,
    Etablissement,
    EvenementInvestigationCasHumain,
    EvenementProduit,
    PositionDossier,
    TemperatureConservation,
)
from ssa.models.evenement_produit import QuantificationUnite
from ssa.widgets import PositionDossierWidget


class WithEvenementCommonMixin(WithEvenementProduitFreeLinksMixin, forms.Form):
    date_reception = forms.DateTimeField(
        label="Date de réception",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "value": timezone.now().strftime("%Y-%m-%d")}),
    )
    numero_rasff = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"pattern": r"^(\d{4}\.\d{4}|AA\d{2}\.\d{4}|\d{6})$", "placeholder": "0000.0000 ou 000000"}
        ),
        label="N° RASFF/AAC",
    )
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={
                "cols": 30,
                "rows": 6,
            }
        ),
        label="Description de l'événement",
    )

    categorie_danger = SEVESChoiceField(
        required=False, choices=CategorieDanger.choices, widget=forms.HiddenInput, label_suffix=""
    )
    precision_danger = forms.CharField(
        required=False,
        label="Précision danger",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Sérotype, molécule...",
            }
        ),
    )

    produit_pret_a_manger = forms.ChoiceField(
        required=False,
        choices=PretAManger.choices,
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        label="Produit Prêt à manger (PAM)",
    )

    @property
    def media(self):
        return super().media + Media(
            css={
                "all": (
                    "ssa/_custom_tree_select.css",
                    "https://cdn.jsdelivr.net/npm/treeselectjs@0.13.1/dist/treeselectjs.css",
                )
            },
            js=(js_module("ssa/categorie_djanger.mjs"), js_module("ssa/free_links.mjs")),
        )

    def categorie_danger_data(self):
        return mark_safe(json.dumps(CategorieDanger.build_options(sorted_results=True)))

    def danger_plus_courants(self):
        return [
            CategorieDanger.LISTERIA_MONOCYTOGENES,
            CategorieDanger.SALMONELLA_ENTERITIDIS,
            CategorieDanger.SALMONELLA_TYPHIMURIUM,
            CategorieDanger.ESCHERICHIA_COLI_SHIGATOXINOGENE,
            CategorieDanger.RESIDU_DE_PESTICIDE_BIOCIDE,
        ]


class EvenementProduitForm(DSFRForm, WithEvenementCommonMixin, forms.ModelForm):
    type_evenement = SEVESChoiceField(choices=TypeEvenement.choices, label="Type d'événement")
    source = SEVESChoiceField(choices=Source.choices, required=False)

    aliments_animaux = forms.ChoiceField(
        required=False,
        choices=[(True, "Oui"), (False, "Non"), (None, "Non applicable")],
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        label="Inclut des aliments pour animaux",
    )

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
        fields = [
            "date_reception",
            "numero_rasff",
            "type_evenement",
            "source",
            "description",
            "aliments_animaux",
            "categorie_produit",
            "denomination",
            "marque",
            "lots",
            "description_complementaire",
            "temperature_conservation",
            "categorie_danger",
            "precision_danger",
            "quantification",
            "quantification_unite",
            "evaluation",
            "produit_pret_a_manger",
            "reference_souches",
            "reference_clusters",
            "actions_engagees",
            "numeros_rappel_conso",
        ]
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


class EtablissementForm(DsfrBaseForm, WithCommonContextVars, BaseEtablissementForm, forms.ModelForm):
    template_name = "ssa/forms/etablissement.html"

    numero_agrement = forms.CharField(
        required=False,
        label="Numéro d'agrément",
        widget=forms.TextInput(attrs={"pattern": r"^\d{2,3}\.\d{2,3}\.\d{2,3}$", "placeholder": "00(0).00(0).00(0)"}),
    )
    type_exploitant = forms.CharField(
        label="Type d'établissement",
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

    class Meta:
        model = Etablissement
        fields = [
            "type_exploitant",
            "position_dossier",
            "siret",
            "numero_agrement",
            "autre_identifiant",
            "raison_sociale",
            "enseigne_usuelle",
            "adresse_lieu_dit",
            "commune",
            "code_insee",
            "departement",
            "pays",
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


class CompteRenduDemandeInterventionForm(BaseCompteRenduDemandeInterventionForm):
    recipients = ContactModelMultipleChoiceField(
        queryset=Contact.objects.get_ssa_structures(), label="Destinataires", required=True
    )


class InvestigationCasHumainForm(DsfrBaseForm, WithEvenementCommonMixin, forms.ModelForm):
    template_name = "ssa/forms/investigation_cas_humain.html"

    source = SEVESChoiceField(choices=SourceInvestigationCasHumain.choices, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._add_free_links(model=EvenementProduit)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_rasff")

    def danger_plus_courants(self):
        return [
            CategorieDanger.LISTERIA_MONOCYTOGENES,
            CategorieDanger.ESCHERICHIA_COLI_SHIGATOXINOGENE,
            CategorieDanger.SALMONELLA_ENTERITIDIS,
            CategorieDanger.SALMONELLA_TYPHIMURIUM,
            CategorieDanger.YERSINIA_ENTEROCOLITICA,
            CategorieDanger.CLOSTRIDIUM_BOTULINUM,
            CategorieDanger.VIRUS_DE_L_ENCEPHALITE_A_TIQUE,
        ]

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS

        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance

    class Meta:
        model = EvenementInvestigationCasHumain
        fields = (
            "date_reception",
            "numero_rasff",
            "source",
            "description",
            "categorie_danger",
            "precision_danger",
            "reference_souches",
            "reference_clusters",
            "evaluation",
        )
        widgets = {
            "evaluation": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Éléments d’interprétation sur les analyses génomiques et autres éléments épidémiologiques"
                    )
                },
            )
        }

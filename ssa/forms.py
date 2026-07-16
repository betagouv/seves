from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.forms import ChoiceField, Media
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from core.fields import ContactModelMultipleChoiceField, DSFRRadioButton, SEVESChoiceField
from core.form_mixins import DSFRForm, WithLatestVersionLocking, js_module
from core.forms import BaseCompteRenduDemandeInterventionForm, BaseEtablissementForm
from core.mixins import WithCommonContextVars, WithEtatMixin
from core.models import Contact
from core.widgets import TreeselectRadio
from ssa.constants import (
    CategorieDanger,
    CategorieProduit,
    PretAManger,
    Source,
    SourceInvestigationCasHumain,
    TypeEvenement,
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
from ssa.models.evenement_produit import EvenementProduitReadOnly, QuantificationUnite
from ssa.widgets import PositionDossierWidget


class WithEvenementCommonMixin(WithEvenementProduitFreeLinksMixin, forms.Form):
    date_reception = forms.DateField(
        label="Date de réception",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    numero_rasff = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "0000.0000 ou 000000"}),
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

    precision_danger = forms.CharField(
        required=False,
        label="Précision danger",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Sérotype, molécule...",
            }
        ),
    )

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("ssa/categorie_danger_produit_messages.mjs"), js_module("ssa/free_links.mjs")),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localtime(timezone.now()).date().isoformat()
        self.fields["date_reception"].initial = today
        self.fields["date_reception"].widget.attrs["max"] = today


class EvenementProduitForm(DSFRForm, WithEvenementCommonMixin, WithLatestVersionLocking, forms.ModelForm):
    CategorieDanger = CategorieDanger

    type_evenement = SEVESChoiceField(choices=TypeEvenement.choices, label="Type d'événement")
    source = SEVESChoiceField(choices=Source.choices, required=True)

    aliments_animaux = forms.ChoiceField(
        required=False,
        choices=[(True, "Oui"), (False, "Non")],
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        label="Inclut des aliments pour animaux",
    )

    categorie_produit = ChoiceField(
        required=False, choices=CategorieProduit, widget=TreeselectRadio(choices=CategorieProduit.treeselect_groups)
    )
    categorie_danger = ChoiceField(
        required=False,
        choices=CategorieDanger,
        widget=TreeselectRadio(
            choices=CategorieDanger.treeselect_choices_with_dangers_courants(CategorieDanger.danger_courants_ssa_pc)
        ),
    )

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
    produit_pret_a_manger = forms.ChoiceField(
        required=False,
        choices=PretAManger.choices,
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        label="Produit Prêt à manger (PAM)",
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
        self.maestro_reference = kwargs.pop("maestro_reference", "")
        super().__init__(*args, **kwargs)
        self._add_free_links(model=EvenementProduitReadOnly)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_rasff")
        if not self.instance.pk and self.maestro_reference:
            self.fields["source"].initial = Source.PRELEVEMENT_PSPC.value
            self.fields["description"].initial = f"Référence Maestro : {self.maestro_reference}"

    def clean(self):
        super().clean()
        if self.cleaned_data["categorie_danger"] not in CategorieDanger.dangers_bacteriens():
            self.cleaned_data["produit_pret_a_manger"] = ""

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS
            self.instance.date_publication = timezone.now()

        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure

        if self.maestro_reference:
            self.instance.maestro_reference = self.maestro_reference

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
            "latest_version",
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
            "code_postal",
            "departement",
            "pays",
            "numeros_resytal",
        ]


class CompteRenduDemandeInterventionForm(BaseCompteRenduDemandeInterventionForm):
    recipients = ContactModelMultipleChoiceField(
        queryset=Contact.objects.get_ssa_structures(), label="Destinataires", required=True
    )


class InvestigationCasHumainForm(DsfrBaseForm, WithEvenementCommonMixin, WithLatestVersionLocking, forms.ModelForm):
    template_name = "ssa/forms/investigation_cas_humain.html"

    categorie_danger = ChoiceField(
        required=False,
        choices=CategorieDanger,
        widget=TreeselectRadio(
            choices=CategorieDanger.treeselect_choices_with_dangers_courants(CategorieDanger.danger_courants_ssa_ich)
        ),
    )

    source = SEVESChoiceField(choices=SourceInvestigationCasHumain.choices, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._add_free_links(model=EvenementProduitReadOnly)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_rasff")

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS
            self.instance.date_publication = timezone.now()

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
            "latest_version",
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

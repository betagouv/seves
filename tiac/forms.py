from copy import copy
from functools import cached_property
import re

from django import forms
from django.conf import settings
from django.contrib.postgres.forms import SimpleArrayField
from django.forms import Field, Media
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from core.fields import ContactModelMultipleChoiceField, MultiModelChoiceField, SEVESChoiceField
from core.form_mixins import WithFreeLinksMixin, WithLatestVersionLocking, js_module
from core.forms import BaseCompteRenduDemandeInterventionForm, BaseEtablissementForm, SetMultipleChoiceField
from core.mixins import WithEtatMixin
from core.models import Contact, Departement, Structure
from core.widgets import Treeselect, TreeselectGroup
from ssa.constants import CategorieDanger, CategorieProduit
from ssa.models import EvenementProduit
from tiac.constants import (
    DANGERS_COURANTS,
    DangersSyndromiques,
    EtatPrelevement,
    EvenementFollowUp,
    EvenementOrigin,
    ModaliteDeclarationEvenement,
    Motif,
    MotifAliment,
    SuspicionConclusion,
    TypeAliment,
    TypeCollectivite,
    TypeRepas,
)
from tiac.fields import SelectWithAttributeField
from tiac.models import (
    AlimentSuspect,
    AnalyseAlimentaire,
    Analyses,
    Etablissement,
    EvenementSimple,
    InvestigationFollowUp,
    InvestigationTiac,
    RepasSuspect,
    validate_resytal,
)


class EvenementSimpleForm(DsfrBaseForm, WithFreeLinksMixin, WithLatestVersionLocking, forms.ModelForm):
    date_reception = forms.DateTimeField(
        label="Date de réception",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "value": timezone.now().strftime("%Y-%m-%d")}),
    )
    evenement_origin = SEVESChoiceField(
        choices=EvenementOrigin.choices,
        label="Signalement déclaré par",
        required=False,
    )
    nb_sick_persons = forms.IntegerField(required=False, label="Nombre de malades total")
    follow_up = SEVESChoiceField(choices=EvenementFollowUp.choices, label="Suite donnée", required=True)
    modalites_declaration = forms.ChoiceField(
        required=False,
        choices=ModaliteDeclarationEvenement.choices,
        widget=forms.RadioSelect,
        label="Modalités de déclaration",
    )

    class Meta:
        model = EvenementSimple
        fields = (
            "date_reception",
            "evenement_origin",
            "modalites_declaration",
            "contenu",
            "notify_ars",
            "nb_sick_persons",
            "follow_up",
            "latest_version",
        )
        widgets = {
            "notify_ars": forms.RadioSelect(choices=((True, "Oui"), (False, "Non"))),
        }

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("ssa/free_links.mjs"),
                js_module("tiac/evenement_simple.mjs"),
                js_module("tiac/ars_informee.mjs"),
            ),
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._add_free_links()

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS

        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance

    def _add_free_links(self, model=None):
        instance = getattr(self, "instance", None)

        queryset = (
            EvenementSimple.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementSimple.Etat.BROUILLON)
        )
        if instance:
            queryset = queryset.exclude(id=instance.id)

        queryset_evenement_produit = (
            EvenementProduit.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        queryset_investigation_tiac = (
            InvestigationTiac.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                ("Enregistrement simple", queryset),
                ("Événement produit", queryset_evenement_produit),
                ("Investigation de tiac", queryset_investigation_tiac),
            ],
        )


class CompteRenduDemandeInterventionForm(BaseCompteRenduDemandeInterventionForm):
    recipients = ContactModelMultipleChoiceField(
        queryset=Contact.objects.get_tiac_structures(), label="Destinataires", required=True
    )


class EtablissementForm(DsfrBaseForm, BaseEtablissementForm, forms.ModelForm):
    template_name = "tiac/forms/etablissement.html"

    siret = forms.CharField(
        label="N° SIRET",
        label_suffix="",
        required=False,
        max_length=14,
        widget=forms.Select(attrs={"hidden": "hidden"}),
    )
    type_etablissement = forms.CharField(
        required=False,
        label="Type d'établissement",
        widget=forms.TextInput(attrs={"placeholder": "Lieu d'achat, restaurant, centre d'expédition…"}),
    )

    date_inspection = forms.DateTimeField(
        required=False,
        label="Date d'inspection",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["numero_resytal"].field.widget.attrs.update(
            {
                "pattern": re.sub(r"\\+", r"\\", validate_resytal.regex.pattern),
                "data-errormessage": validate_resytal.message,
                "placeholder": "25-000000",
            }
        )
        if self.instance and self.instance.siret:
            self["siret"].field.widget.choices = ((self.instance.siret, f"{self.instance.siret} (Forcer la valeur)"),)

    class Meta:
        model = Etablissement
        fields = [
            "type_etablissement",
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
            "has_inspection",
            "numero_resytal",
            "date_inspection",
            "evaluation",
            "commentaire",
        ]
        widgets = {"code_insee": forms.HiddenInput}


class EvenementSimpleTransferForm(DsfrBaseForm, forms.ModelForm):
    transfered_to = forms.ModelChoiceField(
        queryset=Structure.objects.only_DD(),
        label="Sélectionner une structure",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["follow_up"].initial = EvenementFollowUp.TRANSMISSION_DD

    class Meta:
        model = EvenementSimple
        fields = ["transfered_to", "follow_up"]
        widgets = {
            "follow_up": forms.HiddenInput(),
        }


class SuspicionConclusionSelectedHazardField(SetMultipleChoiceField):
    def valid_value(self, value):
        return True


class InvestigationTiacForm(DsfrBaseForm, WithFreeLinksMixin, WithLatestVersionLocking, forms.ModelForm):
    SuspicionConclusion = SuspicionConclusion
    CategorieDanger = CategorieDanger
    DangersSyndromiques = DangersSyndromiques

    date_reception = forms.DateTimeField(
        required=False,
        label="Date de réception",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "value": timezone.now().strftime("%Y-%m-%d")}),
    )
    evenement_origin = SEVESChoiceField(
        choices=EvenementOrigin.choices,
        label="Signalement déclaré par",
        required=False,
    )
    modalites_declaration = forms.ChoiceField(
        required=False,
        choices=ModaliteDeclarationEvenement.choices,
        widget=forms.RadioSelect,
        label="Modalités de déclaration",
    )
    numero_sivss = forms.CharField(
        required=False,
        label="N° SIVSS de l'ARS",
        widget=forms.TextInput(
            attrs={"placeholder": "000000", "pattern": r"\d{6}", "maxlength": 6, "title": "6 chiffres requis"}
        ),
    )
    follow_up = forms.ChoiceField(
        choices=InvestigationFollowUp.choices, widget=forms.RadioSelect, label="Suite donnée", required=True
    )

    nb_sick_persons = forms.IntegerField(required=False, label="Nombre de malades total")
    nb_sick_persons_to_hospital = forms.IntegerField(required=False, label="Dont conduits à l'hôpital")
    nb_dead_persons = forms.IntegerField(required=False, label="Dont décédés")
    datetime_first_symptoms = forms.DateTimeField(
        required=False,
        label="Première date et heure d'apparition des symptômes",
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
            },
        ),
    )

    datetime_last_symptoms = forms.DateTimeField(
        required=False,
        label="Dernière date et heure d'apparition des symptômes",
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
            },
        ),
    )

    danger_syndromiques_suspectes_display = forms.ChoiceField(
        choices=DangersSyndromiques.choices, widget=forms.RadioSelect, label="", required=False
    )
    danger_syndromiques_suspectes = SimpleArrayField(
        forms.CharField(), delimiter="||", required=False, widget=forms.HiddenInput
    )
    analyses_sur_les_malades = forms.ChoiceField(
        choices=Analyses.choices,
        widget=forms.RadioSelect(
            attrs={
                "data-action": "change->etiologie-form#onAnalyseChange",
                "data-etiologie-form-target": "analyses",
            }
        ),
        label="Analyses engagées sur les malades",
        required=False,
    )
    precisions = forms.CharField(
        widget=forms.TextInput(attrs={"disabled": True}), required=False, label="Précisions", help_text="Type d'analyse"
    )
    agents_confirmes_ars = SetMultipleChoiceField(
        required=False,
        choices=CategorieDanger,
        widget=Treeselect(
            choices=(
                TreeselectGroup(
                    value=None,
                    label="Dangers les plus courants",
                    choices=[(it.value, str(it)) for it in DANGERS_COURANTS],
                ),
                TreeselectGroup(value=None, label="Liste complète des dangers", choices=CategorieDanger),
            ),
        ),
    )

    suspicion_conclusion = SEVESChoiceField(
        label="Conclusion de la suspicion de TIAC", choices=SuspicionConclusion, required=False
    )
    selected_hazard = SuspicionConclusionSelectedHazardField(
        label="Dangers retenus", choices=(), required=False, widget=Treeselect
    )

    class Meta:
        model = InvestigationTiac
        fields = (
            "date_reception",
            "evenement_origin",
            "modalites_declaration",
            "contenu",
            "notify_ars",
            "will_trigger_inquiry",
            "numero_sivss",
            "follow_up",
            "nb_sick_persons",
            "nb_sick_persons_to_hospital",
            "nb_dead_persons",
            "datetime_first_symptoms",
            "datetime_last_symptoms",
            "danger_syndromiques_suspectes",
            "analyses_sur_les_malades",
            "precisions",
            "agents_confirmes_ars",
            "suspicion_conclusion",
            "selected_hazard",
            "conclusion_comment",
            "conclusion_repas",
            "conclusion_aliment",
            "latest_version",
        )
        widgets = {
            "notify_ars": forms.RadioSelect(choices=((True, "Oui"), (False, "Non"))),
            "will_trigger_inquiry": forms.RadioSelect(choices=((True, "Oui"), (False, "Non"))),
        }

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("ssa/free_links.mjs"),
                js_module("tiac/etiologie.mjs"),
                js_module("tiac/tiac_conclusion.mjs"),
                js_module("tiac/ars_informee.mjs"),
            ),
        )

    @cached_property
    def selected_hazard_empty(self):
        field = copy(self.fields["selected_hazard"])
        field.disabled = True
        return Field.get_bound_field(field, self, "selected_hazard")

    @cached_property
    def selected_hazard_suspected_choices(self):
        field = copy(self.fields["selected_hazard"])
        field.disabled = False
        field.widget = Treeselect(attrs=field.widget.attrs.copy(), category_separator=None)
        field.choices = DangersSyndromiques
        return Field.get_bound_field(field, self, "selected_hazard")

    @cached_property
    def selected_hazard_confirmed_choices(self):
        field = copy(self.fields["selected_hazard"])
        field.disabled = False
        field.choices = CategorieDanger
        field.widget = Treeselect(
            attrs=field.widget.attrs.copy(),
            choices=(
                TreeselectGroup(
                    value=None,
                    label="Dangers les plus courants",
                    choices=[(it.value, str(it)) for it in DANGERS_COURANTS],
                ),
                TreeselectGroup(value=None, label="Liste complète des dangers", choices=CategorieDanger),
            ),
        )
        return Field.get_bound_field(field, self, "selected_hazard")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._add_free_links()
        for field in ("conclusion_repas", "conclusion_aliment"):
            self[field].field.empty_label = settings.SELECT_EMPTY_CHOICE
            queryset = self[field].field.queryset
            self[field].field.queryset = (
                queryset.filter(investigation=self.instance) if self.instance.pk else queryset.none()
            )

    def clean_suspicion_conclusion_and_selected_hazard(self):
        suspicion_conclusion = self.cleaned_data.get("suspicion_conclusion")
        selected_hazard = self.cleaned_data.get("selected_hazard")

        if suspicion_conclusion not in (SuspicionConclusion.CONFIRMED, SuspicionConclusion.SUSPECTED):
            self.cleaned_data["selected_hazard"] = []
        elif suspicion_conclusion == SuspicionConclusion.CONFIRMED and any(
            item not in CategorieDanger.values for item in selected_hazard
        ):
            self.add_error(
                "selected_hazard", f"La valeur doit être comprise parmis [{', '.join(CategorieDanger.labels)}]"
            )
        elif suspicion_conclusion == SuspicionConclusion.SUSPECTED and any(
            item not in DangersSyndromiques.values for item in selected_hazard
        ):
            self.add_error(
                "selected_hazard", f"La valeur doit être comprise parmis [{', '.join(DangersSyndromiques.labels)}]"
            )

    def clean(self):
        self.clean_suspicion_conclusion_and_selected_hazard()
        return super().clean()

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS

        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance

    def _add_free_links(self, model=None):
        instance = getattr(self, "instance", None)

        queryset = (
            InvestigationTiac.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementSimple.Etat.BROUILLON)
        )
        if instance:
            queryset = queryset.exclude(id=instance.id)

        queryset_evenement_produit = (
            EvenementProduit.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        queryset_evenement_simple = (
            EvenementSimple.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                ("Investigation de tiac", queryset),
                ("Enregistrement simple", queryset_evenement_simple),
                ("Événement produit", queryset_evenement_produit),
            ],
        )


class RepasSuspectForm(DsfrBaseForm, forms.ModelForm):
    template_name = "tiac/forms/repas_suspect.html"

    denomination = forms.CharField(
        label="Dénomination", required=True, widget=forms.TextInput(attrs={"required": "required"})
    )
    menu = forms.CharField(widget=forms.Textarea(attrs={"cols": 30, "rows": 3}), label="Menu", required=False)
    type_repas = SEVESChoiceField(
        required=True,
        choices=TypeRepas.choices,
        label="Type de repas",
        widget=SelectWithAttributeField(attrs={"required": "required"}),
    )
    datetime_repas = forms.DateTimeField(
        required=False,
        label="Date et heure du repas",
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
            },
        ),
    )
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.order_by("numero").all(),
        to_field_name="numero",
        required=False,
        label="Département",
        empty_label=settings.SELECT_EMPTY_CHOICE,
    )
    type_collectivite = SEVESChoiceField(required=False, choices=TypeCollectivite.choices, label="Type de collectivité")
    motif_suspicion = forms.MultipleChoiceField(
        choices=Motif.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Motif de suspicion du repas",
    )

    class Meta:
        model = RepasSuspect
        fields = [
            "denomination",
            "menu",
            "type_repas",
            "datetime_repas",
            "nombre_participant",
            "departement",
            "type_collectivite",
            "motif_suspicion",
        ]


class AlimentSuspectForm(DsfrBaseForm, forms.ModelForm):
    template_name = "tiac/forms/aliment_suspect.html"

    denomination = forms.CharField(
        label="Dénomination de l'aliment", required=True, widget=forms.TextInput(attrs={"required": "required"})
    )
    type_aliment = forms.ChoiceField(
        label="Type d'aliment suspecté", widget=forms.RadioSelect, choices=TypeAliment.choices, required=False
    )
    categorie_produit = SetMultipleChoiceField(required=False, choices=CategorieProduit, widget=Treeselect)
    description_composition = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 3}),
        label="Description de la composition de l'aliment",
        required=False,
    )
    description_produit = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 3}),
        label="Description produit et emballage",
        required=False,
        help_text="Marque, n° de lot, DLC…",
    )
    motif_suspicion = forms.MultipleChoiceField(
        choices=MotifAliment.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Motif de suspicion de l'aliment",
    )

    def clean_categorie_produit(self):
        result = self.cleaned_data.get("categorie_produit")
        if isinstance(result, list):
            return ",".join(list(sorted(set(result))))
        return result

    class Meta:
        model = AlimentSuspect
        fields = [
            "denomination",
            "type_aliment",
            "categorie_produit",
            "description_composition",
            "description_produit",
            "motif_suspicion",
        ]


class AnalyseAlimentaireForm(DsfrBaseForm, forms.ModelForm):
    template_name = "tiac/forms/analyse_alimentaire.html"

    reference_prelevement = forms.CharField(
        label="Référence du prélèvement", required=True, widget=forms.TextInput(attrs={"required": "required"})
    )
    etat_prelevement = SEVESChoiceField(
        label="État du prélèvement",
        required=False,
        choices=EtatPrelevement.choices,
        widget=forms.Select,
    )

    categorie_danger = SetMultipleChoiceField(
        choices=CategorieDanger,
        widget=Treeselect(
            choices=(
                TreeselectGroup(
                    value=None,
                    label="Dangers les plus courants",
                    choices=[(it.value, str(it)) for it in DANGERS_COURANTS],
                ),
                TreeselectGroup(value=None, label="Liste complète des dangers", choices=CategorieDanger),
            ),
        ),
    )

    class Meta:
        model = AnalyseAlimentaire
        exclude = ("investigation",)
        widgets = {
            "sent_to_lnr_cnr": forms.RadioSelect(choices=((True, "Oui"), (False, "Non"))),
        }

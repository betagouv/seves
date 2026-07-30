from django import forms
from django.conf import settings
from django.forms import Media
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_countries.fields import CountryField
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField
from core.form_mixins import js_module
from core.models import Departement
from sa.forms.fields import LatLonField
from sa.models import Espece, Maladie
from sa.models.evenement import ContexteSuspicion, EvenementAnimal, HumanInvolved, StatutAnimal, TypeDetenteur


class EvenementAnimalPreCreationForm(DsfrBaseForm):
    maladie = forms.ModelChoiceField(queryset=Maladie.objects.all())
    espece = forms.ModelChoiceField(queryset=Espece.objects.all())
    statut_animal = forms.ChoiceField(
        required=True,
        choices=StatutAnimal,
        widget=forms.RadioSelect(attrs={"class": "fr-fieldset__element--inline"}),
        label="Statut de l'animal",
    )


class EvenementAnimalForm(DsfrBaseForm, forms.ModelForm):
    type_detenteur = forms.ChoiceField(
        choices=TypeDetenteur.choices,
        initial=TypeDetenteur.ETABLISSEMENT,
        required=True,
        widget=forms.RadioSelect,
    )

    date_statut_changed = forms.DateField(
        required=True,
        label=mark_safe("<span class='label-marked'>Date à prendre en compte pour le changement de statut</span>"),
        help_text="À mettre à jour lors de la modification manuelle du statut",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    departement_etablissement = forms.ModelChoiceField(
        queryset=Departement.objects.order_by("numero").all(),
        to_field_name="numero",
        required=False,
        empty_label=settings.SELECT_EMPTY_CHOICE,
        label="Département",
    )
    pays_etablissement = CountryField(blank=True).formfield(
        label="Pays", empty_label=settings.SELECT_EMPTY_CHOICE, widget=forms.Select(attrs={"class": "fr-select"})
    )

    departement_particulier = forms.ModelChoiceField(
        queryset=Departement.objects.order_by("numero").all(),
        to_field_name="numero",
        required=False,
        empty_label=settings.SELECT_EMPTY_CHOICE,
        label="Département",
    )

    # Localisation
    adresse_lieu_dit = forms.CharField(
        label="Adresse ou lieu-dit", required=False, widget=forms.Select(attrs={"hidden": "hidden"})
    )
    type_lieu = SEVESChoiceField(
        choices=StatutAnimal.choices,
        label="Type de lieu",
        widget=forms.Select(attrs={"required": True}),
    )
    coordinates = LatLonField(
        required=True,
        label="",
    )

    context_suspicion = SEVESChoiceField(
        choices=ContexteSuspicion.choices,
        required=False,
        label="Contexte de la suspicion",
        help_text="Contexte d'identification de la suspicion",
    )
    date_first_symptoms = forms.DateField(
        required=False,
        label="Date d'apparition des éventuels 1ers symptômes",
        help_text="À défaut date de la suspicion",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    human_involved = forms.ChoiceField(
        choices=HumanInvolved.choices,
        widget=forms.RadioSelect(attrs={"class": "fr-fieldset__element--inline"}),
        label="Humains exposés pour lesquels des actions sont engagées ?",
        required=False,
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "cols": 30,
                "rows": 10,
                "placeholder": "Circonstances de la suspicion, investigations engagées, précisions sur la date des symptômes ou sur les conditions du prélèvement",
            }
        ),
        label="Description de la situation",
    )

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("core/map.mjs"),
                js_module("core/address_search_autocomplete.mjs"),
                js_module("sa/detenteur.mjs"),
            ),
        )

    class Meta:
        model = EvenementAnimal
        fields = [
            "maladie",
            "espece",
            "statut_animal",
            "statut_evenement",
            "date_statut_changed",
            # Détenteur etablissement
            "numero_identifiant_etablissement",
            "raison_sociale_etablissement",
            "departement_etablissement",
            "autre_identifiant_etablissement",
            "adresse_lieu_dit_etablissement",
            "code_insee_etablissement",
            "siret_etablissement",
            "commune_etablissement",
            "pays_etablissement",
            # Détenteur particulier
            "nom_particulier",
            "prenom_particulier",
            "adresse_particulier",
            "commune_particulier",
            "departement_particulier",
            "code_insee_particulier",
            "email_particulier",
            "telephone_particulier",
            # Localisation
            "adresse_lieu_dit",
            "commune",
            "code_insee",
            "numero_identifiant",
            "type_lieu",
            "coordinates",
            "context_suspicion",
            "date_first_symptoms",
            "human_involved",
            "description",
        ]
        widgets = {
            "maladie": forms.HiddenInput,
            "espece": forms.HiddenInput,
            "statut_animal": forms.HiddenInput,
            "code_insee": forms.HiddenInput,
            "commune": forms.Select(attrs={"hidden": "hidden"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.maladie = kwargs.pop("maladie")
        self.espece = kwargs.pop("espece")
        self.statut_animal = kwargs.pop("statut_animal")
        self.structure = kwargs.pop("structure")
        super().__init__(*args, **kwargs)
        self.fields["maladie"].initial = self.maladie
        self.fields["espece"].initial = self.espece
        self.fields["statut_animal"].initial = self.statut_animal

        today = timezone.localtime(timezone.now()).date().isoformat()
        self.fields["date_statut_changed"].widget.attrs["max"] = today
        self.fields["date_first_symptoms"].widget.attrs["max"] = today

        type_detenteur = self.fields["type_detenteur"].initial
        if self.is_bound:
            type_detenteur = self.data.get("type_detenteur")
        if type_detenteur == TypeDetenteur.PARTICULIER:
            self.fields["numero_identifiant_etablissement"].required = False
            self.fields["nom_particulier"].required = True
        else:
            self.fields["numero_identifiant_etablissement"].required = True
            self.fields["nom_particulier"].required = False

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        return instance

    def clean(self):
        cleaned_data = super().clean()
        type_detenteur = cleaned_data.get("type_detenteur")

        if type_detenteur == TypeDetenteur.ETABLISSEMENT:
            particulier_fields = (
                "nom_particulier",
                "prenom_particulier",
                "adresse_particulier",
                "commune_particulier",
                "departement_particulier",
                "code_insee_particulier",
                "email_particulier",
                "telephone_particulier",
            )
            for field in particulier_fields:
                self.cleaned_data.pop(field, None)
        elif type_detenteur == TypeDetenteur.PARTICULIER:
            etablissement_fields = (
                "numero_identifiant_etablissement",
                "raison_sociale_etablissement",
                "departement_etablissement",
                "autre_identifiant_etablissement",
                "adresse_lieu_dit_etablissement",
                "code_insee_etablissement",
                "siret_etablissement",
                "commune_etablissement",
                "pays_etablissement",
            )
            for field in etablissement_fields:
                self.cleaned_data.pop(field, None)

        return cleaned_data

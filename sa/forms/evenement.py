from django import forms
from django.forms import Media
from django.utils import timezone
from django.utils.safestring import mark_safe
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField
from core.form_mixins import js_module
from sa.forms.fields import LatLonField
from sa.models import Espece, Maladie
from sa.models.evenement import ContexteSuspicion, EvenementAnimal, HumanInvolved, StatutAnimal


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
    date_statut_changed = forms.DateField(
        required=True,
        label=mark_safe("<span class='label-marked'>Date à prendre en compte pour le changement de statut</span>"),
        help_text="À mettre à jour lors de la modification manuelle du statut",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
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
            js=(js_module("core/map.mjs"), js_module("core/address_search_autocomplete.mjs")),
        )

    class Meta:
        model = EvenementAnimal
        fields = [
            "maladie",
            "espece",
            "statut_animal",
            "statut_evenement",
            "date_statut_changed",
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

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        return instance

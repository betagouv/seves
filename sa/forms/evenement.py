from django import forms
from django.utils import timezone
from django.utils.safestring import mark_safe
from dsfr.forms import DsfrBaseForm

from sa.models import Espece, Maladie
from sa.models.evenement import EvenementAnimal, StatutAnimal


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

    class Meta:
        model = EvenementAnimal
        fields = [
            "maladie",
            "espece",
            "statut_animal",
            "statut_evenement",
            "date_statut_changed",
        ]
        widgets = {
            "maladie": forms.HiddenInput,
            "espece": forms.HiddenInput,
            "statut_animal": forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.maladie = kwargs.pop("maladie", "")
        self.espece = kwargs.pop("espece", "")
        self.statut_animal = kwargs.pop("statut_animal", "")
        super().__init__(*args, **kwargs)
        self.fields["maladie"].initial = self.maladie
        self.fields["espece"].initial = self.espece
        self.fields["statut_animal"].initial = self.statut_animal

        today = timezone.localtime(timezone.now()).date().isoformat()
        self.fields["date_statut_changed"].widget.attrs["max"] = today

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        return instance

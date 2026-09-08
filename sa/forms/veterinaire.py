from django import forms
from django.conf import settings
from dsfr.forms import DsfrBaseForm

from core.fields import DSFRCheckboxSelectMultiple, DSFRRadioButton
from core.models import Departement
from sa.models import Espece
from sa.models.veterinaire import TypeVeterinaire, Veterinaire


class VeterinaireForm(DsfrBaseForm, forms.ModelForm):
    template_name = "sa/forms/veterinaire.html"

    type_veterinaire = forms.ChoiceField(
        label="Type de vétérinaire",
        choices=TypeVeterinaire.choices,
        initial=TypeVeterinaire.SANITAIRE,
        widget=DSFRRadioButton(attrs={"required": "true"}),
    )
    nom_structure = forms.CharField(
        label="Nom de la structure",
        max_length=255,
        widget=forms.TextInput(attrs={"required": "true"}),
    )
    adresse_lieu_dit = forms.CharField(
        label="Adresse ou lieu-dit", required=False, widget=forms.Select(attrs={"hidden": "hidden"})
    )
    commune = forms.CharField(label="Commune", required=False, widget=forms.Select(attrs={"hidden": "hidden"}))
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.order_by("numero").all(),
        to_field_name="numero",
        required=False,
        empty_label=settings.SELECT_EMPTY_CHOICE,
        label="Département",
    )
    code_insee = forms.CharField(label="Code INSEE", required=False)
    especes = forms.ModelMultipleChoiceField(
        label="Espèces",
        queryset=Espece.objects.none(),
        required=False,
        widget=DSFRCheckboxSelectMultiple(attrs={"class": "fr-checkbox-group fr-mt-1w"}),
    )

    class Meta:
        model = Veterinaire
        exclude = ("evenement",)

    def __init__(self, *args, espece_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not espece_id and self.instance and self.instance.pk:
            espece_id = self.instance.evenement.espece_id

        self.fields["especes"].queryset = Espece.objects.filter(pk=espece_id) if espece_id else Espece.objects.none()
        if espece_id and not self.instance.pk and not self.is_bound:
            self.fields["especes"].initial = [espece_id]

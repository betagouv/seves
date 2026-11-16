from django import forms
from django.conf import settings
from dsfr.forms import DsfrBaseForm

from core.fields import DSFRCheckboxSelectMultiple, DSFRRadioButton
from core.models import Departement
from sa.models.veterinaire import TypeVeterinaire, Veterinaire


class VeterinaireForm(DsfrBaseForm, forms.ModelForm):
    template_name = "sa/forms/veterinaire.html"

    type_veterinaire = forms.ChoiceField(
        label="Type de vétérinaire",
        choices=TypeVeterinaire.choices,
        initial=TypeVeterinaire.SANITAIRE,
        widget=DSFRRadioButton(attrs={"required": "true", "class": "fr-fieldset__element--inline"}),
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
    especes_concernees = forms.MultipleChoiceField(
        label="Espèces",
        required=False,
        widget=DSFRCheckboxSelectMultiple(attrs={"class": "fr-checkbox-group fr-mt-1w"}),
    )

    class Meta:
        model = Veterinaire
        exclude = ("evenement", "especes_concernees")

    def __init__(self, *args, especes_concernees_formset, **kwargs):
        super().__init__(*args, **kwargs)
        self.especes_concernees_formset = especes_concernees_formset

        choices = especes_concernees_formset.veterinaire_choices
        self.fields["especes_concernees"].choices = choices
        if not self.is_bound:
            if self.instance.pk:
                prefixes_by_pk = especes_concernees_formset.prefixes_by_pk
                self.initial["especes_concernees"] = [
                    prefixes_by_pk[pk]
                    for pk in self.instance.especes_concernees.values_list("pk", flat=True)
                    if pk in prefixes_by_pk
                ]
            if len(choices) == 1:
                self.initial["especes_concernees"] = [choices[0][0]]

            for field in ("adresse_lieu_dit", "commune"):
                if value := self.initial.get(field):
                    self.fields[field].widget.choices = [(value, value)]

    def _save_m2m(self):
        super()._save_m2m()
        # Must be called after the especes concernees formset has been saved, as rows are identified by their prefix
        especes_concernees = self.especes_concernees_formset.saved_instances_by_prefix
        if len(especes_concernees) == 1:
            self.instance.especes_concernees.set(especes_concernees.values())
        else:
            self.instance.especes_concernees.set(
                [
                    especes_concernees[prefix]
                    for prefix in self.cleaned_data["especes_concernees"]
                    if prefix in especes_concernees
                ]
            )

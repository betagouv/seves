from django import forms
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from tiac.models import EvenementSimple


class EvenementSimpleForm(DsfrBaseForm, forms.ModelForm):
    template_name = "tiac/forms/evenement_simple.html"

    date_creation = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "date", "disabled": True}), initial=timezone.now
    )

    class Meta:
        model = EvenementSimple
        fields = (
            "createur",
            "date_reception",
            "evenement_origin",
            "modalites_declaration",
            "contenu",
            "notify_ars",
            "nb_sick_persons",
            "follow_up",
            "etablissements",
        )
        widgets = {
            "date_reception": forms.DateTimeInput(attrs={"type": "date"}),
            "modalites_declaration": forms.RadioSelect,
            "notify_ars": forms.RadioSelect(choices=(("true", "Oui"), ("false", "Non"))),
        }

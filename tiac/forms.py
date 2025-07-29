from django import forms
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField
from tiac.constants import EvenementOrigin, EvenementFollowUp
from tiac.models import EvenementSimple


class EvenementSimpleForm(DsfrBaseForm, forms.ModelForm):
    template_name = "tiac/forms/evenement_simple.html"

    date_reception = forms.DateTimeField(
        required=False,
        widget=forms.DateInput(format="%d/%m/%Y", attrs={"type": "date", "value": timezone.now().strftime("%Y-%m-%d")}),
    )
    evenement_origin = SEVESChoiceField(
        choices=EvenementOrigin.choices,
        label="Signalement déclaré par",
        required=False,
    )
    nb_sick_persons = forms.IntegerField(required=False, label="Nombre de malades total")
    follow_up = forms.ChoiceField(
        choices=EvenementFollowUp.choices, widget=forms.RadioSelect, label="Suite donné par la DD", required=True
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
        )
        widgets = {
            "modalites_declaration": forms.RadioSelect,
            "notify_ars": forms.RadioSelect(choices=(("true", "Oui"), ("false", "Non"))),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        return super().save(commit)

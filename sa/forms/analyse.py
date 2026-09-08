import json

from django import forms
from django.db.models import Case, When
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField
from sa.models import Maladie
from sa.models.analyse import Analyse, ResultatAnalyse
from sa.models.laboratoire import Laboratoire, LaboratoireType
from sa.models.methode_analyse import MethodeAnalyse


class AnalyseForm(DsfrBaseForm, forms.ModelForm):
    template_name = "sa/forms/analyse.html"

    maladie = forms.ModelChoiceField(label="Maladie", queryset=Maladie.objects.all())
    date_prelevement = forms.DateField(
        required=True,
        label="Date du prélèvement",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    date_resultat = forms.DateField(
        required=False,
        label="Date du résultat",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    laboratoire = forms.ModelChoiceField(label="Laboratoire", queryset=Laboratoire.objects.none())
    methode = forms.ModelChoiceField(label="Méthode", queryset=MethodeAnalyse.objects.none())
    resultat = SEVESChoiceField(label="Résultat", choices=ResultatAnalyse.choices)

    class Meta:
        model = Analyse
        exclude = ("evenement",)
        widgets = {
            "resultat_confirmation": forms.CheckboxInput,
        }

    def get_laboratoire_queryset(self):
        return Laboratoire.objects.order_by(
            Case(
                When(laboratoire_type=LaboratoireType.LNR, then=0),
                When(laboratoire_type=LaboratoireType.LDA, then=1),
                default=2,
            ),
            "name",
        )

    def get_methode_queryset(self, laboratoire_id):
        if not laboratoire_id:
            return MethodeAnalyse.objects.none()
        return MethodeAnalyse.objects.filter(laboratoires=laboratoire_id)

    @property
    def methodes_par_laboratoire_json(self):
        mapping = {}
        for methode in MethodeAnalyse.objects.prefetch_related("laboratoires"):
            for laboratoire in methode.laboratoires.all():
                mapping.setdefault(str(laboratoire.pk), []).append({"value": methode.pk, "label": methode.libelle})
        return json.dumps(mapping)

    @property
    def laboratoires_types_json(self):
        mapping = {
            str(laboratoire.pk): {
                "type": laboratoire.laboratoire_type,
                "label": laboratoire.get_laboratoire_type_display(),
            }
            for laboratoire in Laboratoire.objects.all()
        }
        return json.dumps(mapping)

    def __init__(self, *args, maladie_initial=None, **kwargs):
        super().__init__(*args, **kwargs)
        if maladie_initial and not self.instance.pk and not self.is_bound:
            self.fields["maladie"].initial = maladie_initial

        self.fields["laboratoire"].queryset = self.get_laboratoire_queryset()

        laboratoire_id = self.data.get(self.add_prefix("laboratoire")) if self.is_bound else None
        if not laboratoire_id and self.instance and self.instance.pk:
            laboratoire_id = self.instance.laboratoire_id
        self.fields["methode"].queryset = self.get_methode_queryset(laboratoire_id)
        if not laboratoire_id:
            self.fields["methode"].widget.attrs["disabled"] = "disabled"

        today = timezone.localtime(timezone.now()).date().isoformat()
        self.fields["date_prelevement"].widget.attrs["max"] = today
        self.fields["date_resultat"].widget.attrs["max"] = today

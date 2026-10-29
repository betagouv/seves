import json

from django import forms
from django.db.models import Case, When
from django.forms import Media
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField
from core.form_mixins import js_module
from core.widgets import TreeselectItem, TreeselectRadio
from sa.models import Maladie
from sa.models.analyse import Analyse, ResultatAnalyse
from sa.models.laboratoire import Laboratoire, LaboratoireType
from sa.models.methode_analyse import MethodeAnalyse


class AnalyseForm(DsfrBaseForm, forms.ModelForm):
    template_name = "sa/forms/analyse.html"

    maladie = forms.ModelChoiceField(
        label="Maladie",
        queryset=Maladie.objects.all(),
        widget=TreeselectRadio(
            choices=Maladie.all_treeselect_choices, attrs={"placeholder": "Rechercher", "required": True}
        ),
    )
    date_prelevement = forms.DateField(
        required=True,
        label="Date du prélèvement",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "required": True}),
    )
    date_resultat = forms.DateField(
        required=False,
        label="Date du résultat",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    methode = forms.ModelChoiceField(label="Méthode", queryset=MethodeAnalyse.objects.none(), required=False)
    resultat = SEVESChoiceField(
        label="Résultat",
        choices=ResultatAnalyse.choices,
        initial=ResultatAnalyse.EN_ATTENTE,
        required=True,
        widget=forms.Select(attrs={"required": True}),
    )
    resultat_confirmation = forms.BooleanField(
        label="Résultat valant confirmation",
        required=False,
        widget=forms.CheckboxInput,
        help_text="En cochant cette case, le résultat sera considéré comme confirmant le foyer, le statut de l’événement passera alors à « Confirmé » s’il ne l’est pas déjà et la date d’effet du statut sera renseignée avec la date du résultat.",
    )

    class Meta:
        model = Analyse
        fields = (
            "maladie",
            "date_prelevement",
            "laboratoire",
            "resultat",
            "date_resultat",
            "methode",
            "resultat_confirmation",
        )

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

        labo_queryset = self.get_laboratoire_queryset()
        self.fields["laboratoire"].queryset = labo_queryset
        self.fields["laboratoire"].widget = TreeselectRadio(
            choices=[
                TreeselectItem(value=labo.pk, label=labo.name, categorised_label=labo.name) for labo in labo_queryset
            ],
            attrs={"placeholder": "Rechercher", "required": True},
        )

        laboratoire_id = self.data.get(self.add_prefix("laboratoire")) if self.is_bound else None
        if not laboratoire_id:
            laboratoire_id = self.initial.get("laboratoire")
        self.fields["methode"].queryset = self.get_methode_queryset(laboratoire_id)
        if not laboratoire_id:
            self.fields["methode"].widget.attrs["disabled"] = "disabled"

        today = timezone.localtime(timezone.now()).date().isoformat()
        self.fields["date_prelevement"].widget.attrs["max"] = today
        self.fields["date_resultat"].widget.attrs["max"] = today

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("resultat") != ResultatAnalyse.EN_ATTENTE and not cleaned_data.get("methode"):
            self.add_error("methode", "La méthode est obligatoire lorsque le résultat n'est pas « En attente ».")
        if cleaned_data.get("resultat") == ResultatAnalyse.EN_ATTENTE:
            cleaned_data["date_resultat"] = None
        return cleaned_data

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("core/form/widgets/treeselect_dsfr.mjs"),
                js_module("core/form/widgets/treeselect.mjs"),
            ),
            css={"all": ("core/form/widgets/treeselect_dsfr.css",)},
        )

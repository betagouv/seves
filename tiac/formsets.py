from django.forms import inlineformset_factory, BaseInlineFormSet, Media

from core.form_mixins import js_module
from core.mixins import WithCommonContextVars
from .constants import TypeAliment
from .forms import EtablissementForm, RepasSuspectForm, AlimentSuspectForm, AnalyseAlimentaireForm
from .models import EvenementSimple, Etablissement, InvestigationTiac, RepasSuspect, AlimentSuspect, AnalyseAlimentaire
from django import forms


class EtablissementBaseFormSet(WithCommonContextVars, BaseInlineFormSet):
    template_name = "tiac/forms/etablissement_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/etablissements.mjs"),),
        )

    def __init__(self, *args, title_level=None, title_classes=None, **kwargs):
        self.title_level = title_level or "h3"
        self.title_classes = title_classes or ""
        super().__init__(*args, **kwargs)

    def get_context(self):
        return {**super().get_context(), "title_level": self.title_level, "title_classes": self.title_classes}


class RepasSuspectBaseFormSet(BaseInlineFormSet):
    template_name = "tiac/forms/repas_suspect_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/repas.mjs"),),
        )


class AlimentSuspectBaseFormSet(BaseInlineFormSet):
    template_name = "tiac/forms/aliment_suspect_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/aliment.mjs"),),
        )

    @property
    def empty_form(self):
        form = super().empty_form
        form.initial.setdefault("type_aliment", TypeAliment.SIMPLE)
        return form


EvenementSimpleEtablissementFormSet = inlineformset_factory(
    EvenementSimple, Etablissement, form=EtablissementForm, formset=EtablissementBaseFormSet, extra=0, can_delete=True
)

InvestigationTiacEtablissementFormSet = inlineformset_factory(
    InvestigationTiac, Etablissement, form=EtablissementForm, formset=EtablissementBaseFormSet, extra=0, can_delete=True
)

RepasFormSet = inlineformset_factory(
    InvestigationTiac, RepasSuspect, form=RepasSuspectForm, formset=RepasSuspectBaseFormSet, extra=0, can_delete=True
)

AlimentFormSet = inlineformset_factory(
    InvestigationTiac,
    AlimentSuspect,
    form=AlimentSuspectForm,
    formset=AlimentSuspectBaseFormSet,
    extra=0,
    can_delete=True,
)


class AnalysesAlimentairesBaseFormSet(BaseInlineFormSet):
    template_name = "tiac/forms/analyse_alimentaire_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/analyse_alimentaire.mjs"),),
        )


AnalysesAlimentairesFormSet = inlineformset_factory(
    InvestigationTiac,
    AnalyseAlimentaire,
    form=AnalyseAlimentaireForm,
    formset=AnalysesAlimentairesBaseFormSet,
    extra=0,
    can_delete=True,
)

import json

from django.forms import inlineformset_factory, BaseInlineFormSet, Media

from core.form_mixins import js_module
from core.mixins import WithCommonContextVars
from ssa.models import CategorieProduit
from .constants import TypeAliment
from .forms import EtablissementForm, RepasSuspectForm, AlimentSuspectForm
from .models import EvenementSimple, Etablissement, InvestigationTiac, RepasSuspect, AlimentSuspect
from django import forms


class EtablissementBaseFormSet(WithCommonContextVars, BaseInlineFormSet):
    template_name = "tiac/forms/etablissement_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/etablissements.mjs"),),
        )


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
    def categorie_produit_data(self):
        return json.dumps(CategorieProduit.build_options())

    @property
    def empty_form(self):
        form = super().empty_form
        form.initial.setdefault("type_aliment", TypeAliment.SIMPLE)
        return form


EtablissementFormSet = inlineformset_factory(
    EvenementSimple, Etablissement, form=EtablissementForm, formset=EtablissementBaseFormSet, extra=0, can_delete=True
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

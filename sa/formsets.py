from django import forms
from django.forms import Media
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from core.form_mixins import js_module
from sa.forms.analyse import AnalyseForm
from sa.forms.veterinaire import VeterinaireForm
from sa.models import Analyse, EvenementAnimal
from sa.models.veterinaire import Veterinaire

MAX_ANALYSES = 5


class AnalyseBaseFormSet(BaseInlineFormSet):
    template_name = "sa/forms/analyse_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("sa/analyse.mjs"),),
        )


AnalyseFormSet = inlineformset_factory(
    EvenementAnimal,
    Analyse,
    form=AnalyseForm,
    formset=AnalyseBaseFormSet,
    extra=0,
    can_delete=True,
    max_num=MAX_ANALYSES,
    validate_max=True,
)

MAX_VETERINAIRES = 5


class VeterinaireBaseFormSet(BaseInlineFormSet):
    template_name = "sa/forms/veterinaire_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("sa/veterinaire.mjs"),),
        )


VeterinaireFormSet = inlineformset_factory(
    EvenementAnimal,
    Veterinaire,
    form=VeterinaireForm,
    formset=VeterinaireBaseFormSet,
    extra=0,
    can_delete=True,
    max_num=MAX_VETERINAIRES,
    validate_max=True,
)

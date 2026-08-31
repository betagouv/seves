from django import forms
from django.forms import Media
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from core.form_mixins import js_module
from sa.forms.analyse import AnalyseForm
from sa.models import Analyse, EvenementAnimal

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

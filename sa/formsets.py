from functools import cached_property

from django import forms
from django.forms import Media
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from core.form_mixins import js_module
from sa.forms.analyse import AnalyseForm
from sa.forms.especes_concernees import EspeceConcerneeForm
from sa.forms.veterinaire import VeterinaireForm
from sa.models import Analyse, EvenementAnimal
from sa.models.especes_concernees import EspeceConcernee
from sa.models.veterinaire import Veterinaire
from sa.referentiels import situation_unite

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


class EspeceConcerneeBaseFormSet(BaseInlineFormSet):
    template_name = "sa/forms/especes_concernees_base_set.html"
    deletion_widget = forms.HiddenInput

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("sa/especes_concernees.mjs"),
                js_module("sa/situation_unite.mjs"),
            ),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.forms:
            first_form = self.forms[0]
            first_form.fields["espece"].disabled = True
            first_form.fields["DELETE"].disabled = True

    @cached_property
    def _situation_unite_rows(self):
        return situation_unite.fetch_rows()

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["situation_unite_rows"] = self._situation_unite_rows
        return kwargs

    @property
    def situation_unite_tree_json(self):
        return situation_unite.build_tree_json_for_especes(self._situation_unite_rows)


EspeceConcerneeFormSet = inlineformset_factory(
    EvenementAnimal,
    EspeceConcernee,
    form=EspeceConcerneeForm,
    formset=EspeceConcerneeBaseFormSet,
    extra=1,
    can_delete=True,
)

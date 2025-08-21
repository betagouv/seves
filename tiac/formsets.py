from django.forms import inlineformset_factory, BaseInlineFormSet, Media

from core.form_mixins import js_module
from .forms import EtablissementForm
from .models import EvenementSimple, Etablissement
from django import forms


class EtablissementBaseFormSet(BaseInlineFormSet):
    template_name = "tiac/forms/etablissement_base_set.html"

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/etablissements.mjs"),),
        )

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if "DELETE" in form.fields:
            form.fields["DELETE"].widget = forms.HiddenInput()


EtablissementFormSet = inlineformset_factory(
    EvenementSimple, Etablissement, form=EtablissementForm, formset=EtablissementBaseFormSet, extra=0, can_delete=True
)

from django.forms import inlineformset_factory, BaseInlineFormSet, Media

from core.form_mixins import js_module
from .forms import EtablissementForm
from .models import EvenementSimple, Etablissement


class EtablissementBaseFormSet(BaseInlineFormSet):
    template_name = "tiac/forms/etablissement_base_set.html"

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("tiac/etablissements.mjs"),),
        )


EtablissementFormSet = inlineformset_factory(
    EvenementSimple, Etablissement, form=EtablissementForm, formset=EtablissementBaseFormSet, extra=10, can_delete=True
)

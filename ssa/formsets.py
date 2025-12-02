from django.forms import Media, inlineformset_factory, BaseInlineFormSet

from core.form_mixins import js_module
from ssa.forms import EtablissementForm
from ssa.models import EvenementInvestigationCasHumain, EvenementProduit
from ssa.models.etablissement import Etablissement


class EtablissementBaseFormSet(BaseInlineFormSet):
    template_name = "ssa/forms/etablissement_formset.html"

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("ssa/etablissement_form.mjs"),),
            css={"all": ("core/_etablissement_card.css", "ssa/_etablissement_card.css")},
        )


EtablissementFormSet = inlineformset_factory(
    EvenementProduit, Etablissement, form=EtablissementForm, formset=EtablissementBaseFormSet, extra=0, can_delete=True
)

InvestigationCasHumainsEtablissementFormSet = inlineformset_factory(
    EvenementInvestigationCasHumain,
    Etablissement,
    form=EtablissementForm,
    formset=EtablissementBaseFormSet,
    extra=0,
    can_delete=True,
)

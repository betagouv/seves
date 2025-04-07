from django.forms import inlineformset_factory

from ssa.forms import EtablissementForm
from ssa.models import EvenementProduit
from ssa.models.etablissement import Etablissement

EtablissementFormSet = inlineformset_factory(
    EvenementProduit, Etablissement, form=EtablissementForm, extra=10, can_delete=False
)

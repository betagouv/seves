from django.contrib.contenttypes.forms import generic_inlineformset_factory

from ssa.forms import EtablissementForm
from ssa.models.etablissement import Etablissement

EtablissementFormSet = generic_inlineformset_factory(Etablissement, form=EtablissementForm, extra=10, can_delete=True)

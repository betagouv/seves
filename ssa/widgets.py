from django import forms

from ssa.models.etablissement import Etablissement


class PositionDossierWidget(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option["attrs"]["data-extra-class"] = Etablissement.get_position_dossier_css_class(value)
        return option

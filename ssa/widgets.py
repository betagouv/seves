from django import forms

from ssa.models.etablissement import PositionDossier


class PositionDossierWidget(forms.Select):
    RED_CASES = [
        PositionDossier.SURVENUE_NON_CONFORMITE,
        PositionDossier.DETECTION_NON_CONFORMITE,
        PositionDossier.DETECTION_ET_SURVENUE_NON_CONFORMITE,
    ]

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            extra_class = "fr-badge--error" if value in self.RED_CASES else "fr-badge--info"
            option["attrs"]["data-extra-class"] = extra_class
        return option

from django import forms

from tiac.constants import TypeRepas


class SelectWithAttributeField(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option["attrs"]["data-needs-type-collectivite"] = (
                "true" if value == TypeRepas.RESTAURATION_COLLECTIVE else "false"
            )
        return option

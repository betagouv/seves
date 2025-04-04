from django import forms

from ssa.models import EvenementProduit


class SelectWithAttributeField(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            for_human_case = value in EvenementProduit.SOURCES_FOR_HUMAN_CASE
            option["attrs"]["data-for-human-case"] = "true" if for_human_case else "false"
        return option

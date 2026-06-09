import json

from django import forms
from django.forms import Media, widgets

from core.form_mixins import js_module
from ssa.constants import CategorieDanger, CategorieProduit
from ssa.models.etablissement import Etablissement


class PositionDossierWidget(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option["attrs"]["data-extra-class"] = Etablissement.get_position_dossier_css_class(value)
        return option


class CategorieProduitLegacyTreeselect(widgets.TextInput):
    Choices = CategorieProduit
    template_name = "ssa/forms/widgets/legacy_treeselect.html"

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("ssa/treeselectjs.umd.js"),
                js_module("ssa/form/widgets/legacy_treeselect.mjs"),
            ),
            css={
                "all": (
                    "https://cdn.jsdelivr.net/npm/treeselectjs@0.13.1/dist/treeselectjs.css",
                    "ssa/form/widgets/_custom_tree_select.css",
                )
            },
        )

    def get_context(self, name, value, attrs):
        return {
            **super().get_context(name, value, attrs),
            "categorie_choices_data": json.dumps(self.Choices.build_options()),
        }


class CategorieDangerLegacyTreeselect(CategorieProduitLegacyTreeselect):
    Choices = CategorieDanger

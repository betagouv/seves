from django import forms
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField
from core.widgets import NumericTextInput, TreeselectRadio
from sa.models import Espece
from sa.models.especes_concernees import EspeceConcernee
from sa.referentiels import situation_unite


class EspeceTreeselectRadio(TreeselectRadio):
    def optgroups(self, name, values, attrs=None):
        self._choices = Espece.treeselect_choices_for_selection(values)
        return super().optgroups(name, values, attrs)


class EspeceConcerneeForm(DsfrBaseForm, forms.ModelForm):
    espece = forms.ModelChoiceField(
        queryset=Espece.objects.all(),
        required=True,
        widget=EspeceTreeselectRadio(attrs={"placeholder": "Rechercher", "required": True}),
        label="Espèce",
    )

    type_lieu = SEVESChoiceField(required=False, label="Type de lieu")
    mode_elevage = SEVESChoiceField(required=False, label="Mode d'élevage")
    type_production = SEVESChoiceField(required=False, label="Type de production")
    type_elevage = SEVESChoiceField(required=False, label="Type d'élevage")

    always_save = False

    DETENU_FIELDS = (
        "presents",
        "abattus",
        "depeuples",
        "vaccines",
        "type_lieu",
        "mode_elevage",
        "type_production",
        "type_elevage",
    )

    def __init__(
        self,
        *args,
        situation_unite_rows=None,
        show_detenu_fields=True,
        identifiant_placeholders=None,
        default_identifiant_placeholder=Espece.IDENTIFIANT_PLACEHOLDER_DETENU,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.show_detenu_fields = show_detenu_fields
        self.identifiant_placeholders = identifiant_placeholders or {}
        self.default_identifiant_placeholder = default_identifiant_placeholder
        self.fields["identifiant"].widget.attrs["placeholder"] = self.identifiant_placeholder
        if not show_detenu_fields:
            for field_name in self.DETENU_FIELDS:
                self.fields.pop(field_name)
            return

        choices = situation_unite.choices_by_level(situation_unite_rows)
        empty_choice = self.fields["type_lieu"].choices[:1]
        self.fields["type_lieu"].choices = empty_choice + choices["type_lieu"]
        self.fields["mode_elevage"].choices = empty_choice + choices["mode_elevage"]
        self.fields["type_production"].choices = empty_choice + choices["type_production"]
        self.fields["type_elevage"].choices = empty_choice + choices["type_elevage"]
        if not self.is_bound:
            self.initial.setdefault("type_lieu", self.instance.type_lieu)
            self.initial.setdefault("mode_elevage", self.instance.mode_elevage)
            self.initial.setdefault("type_production", self.instance.type_production)
            self.initial.setdefault("type_elevage", self.instance.type_elevage)

    @property
    def identifiant_placeholder(self):
        espece_id = str(self["espece"].value() or "")
        return self.identifiant_placeholders.get(espece_id) or self.default_identifiant_placeholder

    def has_changed(self):
        return self.always_save or super().has_changed()

    def clean(self):
        cleaned_data = super().clean()
        if not self.show_detenu_fields:
            return cleaned_data

        type_lieu = cleaned_data.get("type_lieu") or ""
        mode_elevage = cleaned_data.get("mode_elevage") or ""
        type_production = cleaned_data.get("type_production") or ""
        type_elevage = cleaned_data.get("type_elevage") or ""

        if not any((type_lieu, mode_elevage, type_production, type_elevage)):
            self.instance.situation_unite_regle = None
            return cleaned_data

        espece = cleaned_data.get("espece")
        regle = None
        if espece is not None:
            regle = espece.situation_unite_regles.filter(
                type_lieu=type_lieu,
                mode_elevage=mode_elevage,
                type_production=type_production,
                type_elevage=type_elevage,
            ).first()

        if regle is None:
            self.add_error(
                "type_lieu", "La situation renseignée ne correspond pas aux valeurs possibles pour cette espèce."
            )
        else:
            self.instance.situation_unite_regle = regle

        return cleaned_data

    class Meta:
        model = EspeceConcernee
        fields = [
            "espece",
            "identifiant",
            "presents",
            "morts",
            "cas",
            "abattus",
            "depeuples",
            "vaccines",
        ]
        widgets = {
            "presents": NumericTextInput,
            "morts": NumericTextInput,
            "cas": NumericTextInput,
            "abattus": NumericTextInput,
            "depeuples": NumericTextInput,
            "vaccines": NumericTextInput,
        }

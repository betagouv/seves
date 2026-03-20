from copy import deepcopy
import dataclasses
import itertools
import re
from typing import Any, Collection, Iterable, Literal, Mapping

from django.db.models import Choices
from django.forms import Media, widgets
from django.utils.choices import normalize_choices

from core.form_mixins import js_module


@dataclasses.dataclass
class TreeselectGroup:
    value: Any
    label: str
    choices: Choices | Iterable[tuple[Any, str]]


class TreeselectGroupWidget(widgets.ChoiceWidget):
    @property
    def template_name(self):
        return (
            "core/form/widgets/treeselect.html#group"
            if self.group_value
            else "core/form/widgets/treeselect.html#nogroup"
        )

    @property
    def allow_multiple_selected(self):
        return self.parent.allow_multiple_selected

    @property
    def input_type(self):
        return self.parent.input_type

    @property
    def option_template_name(self):
        return self.parent.option_template_name

    @property
    def choices(self):
        return self._choices

    @choices.setter
    def choices(self, value):
        self._choices = deepcopy(value)

    def __init__(self, parent: "Treeselect", value, choices):
        self.parent = parent
        self.group_value = value
        super().__init__(self.parent.attrs, choices)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update(context.pop("widget"))
        context["group"] = self.group_value
        context["group_index"] = self.parent.get_next_id()
        context["can_expand"] = self.choices.get("__can_expand__", True)
        context["aria_controls_prefix"] = f"{name}-fr-treeselect-subgroup"
        if "__self__" in self.choices:
            group_label = self.choices["__self__"]
            context["group_option"] = self.create_option(
                name,
                self.group_value,
                group_label,
                str(self.group_value) in value,
                self.parent.get_next_id(),
                None,
                attrs,
                group_option=True,
            )
        return context

    def optgroups(self, name, value, attrs=None):
        has_selected = False
        for option_label, option_value in self.choices.items():
            if self._is_dunder(option_label):
                continue
            if isinstance(option_value, Mapping):
                yield TreeselectGroupWidget(self.parent, option_label, option_value).get_context(name, value, attrs)
            else:
                selected = (not has_selected or self.parent.allow_multiple_selected) and str(option_value) in value
                has_selected |= selected
                yield self.create_option(
                    name, option_value, option_label, selected, self.parent.get_next_id(), subindex=None, attrs=attrs
                )

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None, *, group_option=False):
        context = super().create_option(name, value, label, selected, index, subindex, attrs)
        context["attrs"]["required"] = False  # `require` on checkboxes forces to check all checkboxes
        context["aria_controls_prefix"] = f"{name}-fr-treeselect-subgroup"
        if group_option:
            context["group_index"] = self.parent.get_next_id()
        return context

    def _is_dunder(self, name):
        """
        Returns True if a __dunder__ name, False otherwise.
        """
        return len(name) > 4 and name[:2] == name[-2:] == "__" and name[2] != "_" and name[-3] != "_"


_UNSET = object()


class Treeselect(widgets.ChoiceWidget):
    allow_multiple_selected = True
    input_type = "checkbox"
    template_name = "core/form/widgets/treeselect.html"
    option_template_name = "core/form/widgets/treeselect.html#option"
    has_search_bar = True
    category_separator = ">"

    @property
    def choices(self) -> dict:
        return self._choices

    @choices.setter
    def choices(self, value):
        if not self._choices:
            self._choices = self._choices_as_dict(value)

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("core/form/widgets/treeselect_dsfr.mjs"),
                js_module("core/form/widgets/treeselect.mjs"),
            ),
            css={"all": ("core/form/widgets/treeselect_dsfr.css",)},
        )

    def __init__(
        self,
        attrs=None,
        choices=(),
        *,
        input_type: Literal["checkbox", "radio"] = None,
        has_search_bar=_UNSET,
        category_separator=_UNSET,
    ):
        self._choices = {}
        self._widget_choices = None

        if input_type is not None:
            self.input_type = input_type
        if has_search_bar is not _UNSET:
            self.has_search_bar = has_search_bar
        if category_separator is not _UNSET:
            self.category_separator = category_separator
        super().__init__(attrs, choices)

    def get_next_id(self):
        if not hasattr(self, "_id_stream"):
            self._id_stream = itertools.count(start=1)
        return next(self._id_stream)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["has_search_bar"] = self.has_search_bar
        return context

    def optgroups(self, name, values, attrs=None):
        for label, group_values in self.choices.items():
            if isinstance(values, dict):
                yield TreeselectGroupWidget(self, label, group_values).get_context(name, values, attrs)
            else:
                # Here `group_values` actually represent a single value
                yield TreeselectGroupWidget(self, None, {label: group_values}).get_context(name, values, attrs)

    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):
        return TreeselectGroupWidget(self, None, choices={label: value}).create_option(
            name, value, label, selected, index, subindex, attrs
        )

    def _choices_as_dict(self, choices) -> dict:
        result = {}

        for item in choices:
            if isinstance(item, TreeselectGroup):
                result[item.label] = self._choices_as_dict(normalize_choices(item.choices))
                if item.value is None:
                    result[item.label]["__can_expand__"] = False
                else:
                    result[item.label]["__self__"] = item.value
                continue

            value, categorised_label = item
            if isinstance(categorised_label, str):
                if self.category_separator:
                    *categories, label = re.split(rf"\s*{self.category_separator}\s*", categorised_label)
                else:
                    categories = []
                    label = categorised_label
            elif isinstance(categorised_label, Collection):
                result[value] = self._choices_as_dict(categorised_label)
                continue
            else:
                categories, label = [], categorised_label

            curr_dict = result
            for part in categories:
                if not part:
                    continue
                curr_dict.setdefault(part, {})
                if not isinstance(curr_dict[part], dict):
                    new_dict = {"__self__": curr_dict[part]}
                    curr_dict[part] = new_dict
                curr_dict = curr_dict[part]
            curr_dict[label] = value
        return result

    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, value, attrs, renderer)

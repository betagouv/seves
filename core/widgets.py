from copy import deepcopy
import itertools
import re
from typing import Iterable, Literal, Mapping

from django.forms import Media, widgets

from core.form_mixins import js_module


class TreeselectGroup(widgets.ChoiceWidget):
    template_name = "core/form/widgets/treeselect.html#group"

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
        for option_value, option_label in self.choices.items():
            if option_value == "__self__":
                continue
            if isinstance(option_label, Mapping):
                yield TreeselectGroup(self.parent, option_value, option_label).get_context(name, value, attrs)
            else:
                selected = (not has_selected or self.parent.allow_multiple_selected) and str(option_value) in value
                has_selected |= selected
                yield self.create_option(
                    name, option_value, option_label, selected, self.parent.get_next_id(), subindex=None, attrs=attrs
                )

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None, *, group_option=False):
        context = super().create_option(name, value, label, selected, index, subindex, attrs)
        if group_option:
            context["group_index"] = self.parent.get_next_id()
        return context


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
        if isinstance(value, Mapping):
            self._choices = value
        else:
            self._choices = self._normalize_choices(value)

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("core/form/widgets/treeselect.mjs"),), css={"all": ("core/form/widgets/treeselect.css",)}
        )

    def __init__(
        self,
        attrs=None,
        choices: Iterable | Mapping = (),
        *,
        input_type: Literal["checkbox", "radio"] | None = None,
        has_search_bar=None,
        category_separator=None,
    ):
        self._widget_choices = None

        if input_type is not None:
            self.input_type = input_type
        if has_search_bar is not None:
            self.has_search_bar = has_search_bar
        if category_separator is not None:
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

    def optgroups(self, name, value, attrs=None):
        for option_value, option_label in self.choices.items():
            yield TreeselectGroup(self, option_value, option_label).get_context(name, value, attrs)

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
        return TreeselectGroup(self, value, choices=(label,)).create_option(
            name, value, label, selected, index, subindex, attrs
        )

    def _normalize_choices(self, choices) -> dict:
        result = {}
        for value, categorised_label in choices:
            *categories, label = re.split(rf"\s*{self.category_separator}\s*", categorised_label)
            curr_dict = result
            for part in categories:
                if not part:
                    continue
                curr_dict.setdefault(part, {})
                if not isinstance(curr_dict[part], dict):
                    new_dict = {"__self__": curr_dict[part]}
                    curr_dict[part] = new_dict
                curr_dict = curr_dict[part]
            curr_dict[value] = label
        return result

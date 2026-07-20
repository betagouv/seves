from __future__ import annotations

import dataclasses
import itertools
import typing

from django.forms import Media, widgets
from django.utils.choices import BaseChoiceIterator
from django.utils.functional import Promise

from core.form_mixins import js_module

if typing.TYPE_CHECKING:
    from typing import Any, Iterable, Literal, TypeAlias

    from django.db.models import Choices

    _Choice: TypeAlias = tuple[Any, Any]
    _ChoiceNamedGroup: TypeAlias = tuple[str, Iterable[_Choice]]
    _Choices: TypeAlias = Iterable["_Choice | _ChoiceNamedGroup | TreeselectGroup | TreeselectItem"] | type[Choices]

_UNSET = type("UNSET", (), {"__bool__": lambda *args: False, "__repr__": lambda *args: "UNSET"})()


@dataclasses.dataclass(kw_only=True)
class TreeselectItem(Promise):
    value: Any
    label: str
    categorised_label: str | None
    html_name_prefix: str | None = None


@dataclasses.dataclass(kw_only=True)
class TreeselectGroup(BaseChoiceIterator, Promise):
    value: Any = _UNSET
    label: str
    choices: _Choices
    categorised_label: str | None
    can_expand: bool = True

    def __post_init__(self):
        self._choices_list = list(self.choices)

    def __getitem__(self, index):
        return self._choices_list[index]

    def __iter__(self):
        return iter(self.choices)


class TreeselectGroupWidget(widgets.ChoiceWidget):
    @property
    def template_name(self):
        return (
            "core/form/widgets/treeselect.html#group"
            if isinstance(self.item, TreeselectGroup)
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

    def __init__(self, parent: "TreeselectMixin", item: TreeselectGroup | TreeselectItem):
        self.parent = parent
        self.item = item
        self.group_label = item.label
        if isinstance(item, TreeselectGroup):
            super().__init__(self.parent.attrs, self.item.choices)
        else:
            super().__init__(self.parent.attrs, ((item.label, item.value),))

    def get_selected(self, option_value, value):
        selected = (not self.parent.has_selected or self.parent.allow_multiple_selected) and str(option_value) in value
        self.parent.has_selected |= selected
        return selected

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        context = super().get_context(name, value, attrs)
        context.update(context.pop("widget"))
        context["group"] = self.group_label
        context["group_index"] = self.parent.get_next_id()
        context["can_expand"] = False
        context["auto_select_children"] = self.parent.auto_select_children
        context["aria_controls_prefix"] = f"{name}-fr-treeselect-subgroup"
        if isinstance(self.item, TreeselectGroup):
            context["can_expand"] = self.item.can_expand
            if self.item.categorised_label:
                attrs["data-categorised-label"] = self.item.categorised_label
            if self.item.value:
                context["group_option"] = self.create_option(
                    name,
                    self.item.value,
                    self.group_label,
                    self.get_selected(self.item.value, value),
                    self.parent.get_next_id(),
                    None,
                    attrs,
                    group_option=True,
                )
        return context

    def optgroups(self, name, value, attrs=None):
        attrs = attrs or {}
        for choice in self.choices:
            if isinstance(choice, TreeselectGroup):
                yield TreeselectGroupWidget(self.parent, choice).get_context(name, value, attrs)
            else:
                if not isinstance(choice, TreeselectItem):
                    choice = TreeselectItem(value=choice[0], label=choice[1], categorised_label=None)
                if choice.categorised_label:
                    attrs["data-categorised-label"] = choice.categorised_label
                if choice.html_name_prefix:
                    name = f"{choice.html_name_prefix}-{name}"
                    selected = str(choice.value) in value
                else:
                    selected = self.get_selected(choice.value, value)

                yield self.create_option(
                    name,
                    choice.value,
                    choice.label,
                    selected,
                    self.parent.get_next_id(),
                    subindex=None,
                    attrs=attrs,
                )

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None, *, group_option=False):
        context = super().create_option(name, value, label, selected, index, subindex, attrs)
        context["attrs"]["required"] = False  # `require` on checkboxes forces to check all checkboxes
        context["aria_controls_prefix"] = f"{name}-fr-treeselect-subgroup"
        if group_option:
            context["group_index"] = self.parent.get_next_id()
        return context


class TreeselectMixin(widgets.ChoiceWidget):
    template_name = "core/form/widgets/treeselect.html"
    option_template_name = "core/form/widgets/treeselect.html#option"
    has_search_bar = True
    auto_select_children = False

    @property
    def choices(self) -> _Choices:
        return self._choices

    @choices.setter
    def choices(self, value):
        # We don't want to forcibly evaluate BaseChoiceIterator here
        if not isinstance(self._choices, (BaseChoiceIterator, Promise, bytes, str)) and not self._choices:
            self._choices = value

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
        choices: _Choices = (),
        *,
        input_type: Literal["checkbox", "radio"] = _UNSET,
        has_search_bar: bool = _UNSET,
    ):
        if input_type is not _UNSET:
            self.input_type = input_type
        if has_search_bar is not _UNSET:
            self.has_search_bar = has_search_bar

        self._choices = ()
        super().__init__(attrs, choices=choices)

    def get_next_id(self):
        if not hasattr(self, "_id_stream"):
            self._id_stream = itertools.count(start=1)
        return next(self._id_stream)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["has_search_bar"] = self.has_search_bar
        context["widget"]["allow_multiple_selected"] = self.allow_multiple_selected
        return context

    def optgroups(self, name, values, attrs=None):
        self.has_selected = False
        for choice in self.choices:
            match choice:
                case TreeselectGroup() | TreeselectItem():
                    yield TreeselectGroupWidget(self, choice).get_context(name, values, attrs)
                case _:
                    label, value = choice
                    yield TreeselectGroupWidget(
                        self, TreeselectItem(label=label, value=value, categorised_label="")
                    ).get_context(name, values, attrs)

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
        return TreeselectGroupWidget(
            self, TreeselectItem(label=str(label), value=value, categorised_label="")
        ).create_option(name, value, label, selected, index, subindex, attrs)


class TreeselectCheckbox(TreeselectMixin):
    allow_multiple_selected = True
    input_type = "checkbox"
    auto_select_children = True

    def __init__(
        self,
        attrs=None,
        choices: _Choices = (),
        *,
        input_type: Literal["checkbox", "radio"] = _UNSET,
        has_search_bar: bool = _UNSET,
        auto_select_children: bool = True,
    ):
        super().__init__(attrs, choices, input_type=input_type, has_search_bar=has_search_bar)
        self.auto_select_children = auto_select_children


class TreeselectRadio(TreeselectMixin):
    allow_multiple_selected = False
    input_type = "radio"

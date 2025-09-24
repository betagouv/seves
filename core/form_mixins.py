import operator
from collections import defaultdict
from copy import deepcopy
from functools import reduce
from typing import Union, Iterable, Tuple

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db.models import QuerySet
from django.db.models.utils import AltersData
from django.forms import Script, BaseForm, BaseFormSet, BaseModelForm, BaseModelFormSet, MediaDefiningClass
from django.forms.utils import ErrorList
from django.utils.datastructures import MultiValueDict
from django.utils.translation import ngettext

from core.fields import MultiModelChoiceField
from core.models import LienLibre


def js_module(src, **attributes):
    attributes["type"] = "module"
    return Script(src, **attributes)


class DSFRForm(forms.Form):
    input_to_class = defaultdict(lambda: "fr-input")
    input_to_class["ClearableFileInput"] = "fr-upload"
    input_to_class["Select"] = "fr-select"
    input_to_class["SelectMultiple"] = "fr-select"
    input_to_class["SelectWithAttributeField"] = "fr-select"
    input_to_class["DSFRRadioButton"] = ""
    input_to_class["DSFRCheckboxSelectMultiple"] = ""
    manual_render_fields = []

    def get_context(self):
        context = super().get_context()
        context["manual_render_fields"] = self.manual_render_fields
        return context

    def as_dsfr_div(self):
        return self.render("core/_dsfr_div.html")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field in self.fields:
            widget = self.fields[field].widget
            class_to_add = self.input_to_class[type(widget).__name__]
            widget.attrs["class"] = widget.attrs.get("class", "") + " " + class_to_add


class WithNextUrlMixin:
    def add_next_field(self, next):
        if next:
            self.fields["next"] = forms.CharField(widget=forms.HiddenInput())
            self.initial["next"] = next


class WithContentTypeMixin:
    def add_content_type_fields(self, obj):
        if obj:
            self.fields["content_type"].widget = forms.HiddenInput()
            self.fields["object_id"].widget = forms.HiddenInput()
            self.initial["content_type"] = ContentType.objects.get_for_model(obj)
            self.initial["object_id"] = obj.pk


class WithFreeLinksMixin:
    model_label = "Unknown"

    def save_free_links(self, instance):
        links_ids_to_keep = []
        for obj in self.cleaned_data["free_link"]:
            link = LienLibre.objects.for_both_objects(obj, instance)

            if link:
                links_ids_to_keep.append(link.id)
            else:
                link = LienLibre.objects.create(related_object_1=instance, related_object_2=obj)
                links_ids_to_keep.append(link.id)

        links_to_delete = LienLibre.objects.for_object(instance).exclude(id__in=links_ids_to_keep)
        links_to_delete.delete()

    def get_queryset(self, model, user, instance):
        raise NotImplementedError

    def _add_free_links(self, model):
        instance = getattr(self, "instance", None)
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                (self.model_label, self.get_queryset(model, self.user, instance)),
            ],
        )

    def clean_free_link(self):
        if self.instance and self.instance in self.cleaned_data["free_link"]:
            raise ValidationError("Vous ne pouvez pas lier un objet a lui-même.")
        return self.cleaned_data["free_link"]


FormLike = Union[BaseForm, BaseFormSet]
ModelFormLike = Union[BaseModelForm, BaseModelFormSet]


class DeclarativeFormMetaclass(MediaDefiningClass):
    def __new__(mcs, name, bases, attrs):
        attrs["declared_form_classes"] = {
            key: attrs.pop(key)
            for key, value in list(attrs.items())
            if isinstance(value, type) and issubclass(value, FormLike)
        }

        new_class = super().__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        declared_form_classes = {}
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, "declared_form_classes"):
                declared_form_classes.update(base.declared_form_classes)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_form_classes:
                    declared_form_classes.pop(attr)

        new_class.base_form_casses = declared_form_classes

        return new_class


class BaseMultiForm(metaclass=DeclarativeFormMetaclass):
    def __init__(
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        form_kwargs=None,
        renderer=None,
    ):
        self.is_bound = data is not None or files is not None
        self.prefix = prefix or self.get_default_prefix()
        self.auto_id = auto_id
        self.data = MultiValueDict() if data is None else data
        self.files = MultiValueDict() if files is None else files
        self.initial = initial or {}
        self.error_class = error_class or ErrorList
        self.form_kwargs = form_kwargs or {}
        self.renderer = renderer
        self._errors = None  # Stores the errors after clean() has been called.
        self.form_classes = deepcopy(self.base_form_casses)

        self._forms_cache = {}

    def __repr__(self):
        if self._errors is None:
            is_valid = "Unknown"
        else:
            is_valid = self.is_bound and not self._errors
        return f"<{self.__class__.__name__} bound={self.is_bound}, valid={is_valid}, form_classes={self.form_classes}>"

    def __iter__(self) -> Iterable[FormLike]:
        for name in self.forms:
            yield self[name]

    def __getitem__(self, name) -> FormLike:
        try:
            return self.forms[name]
        except KeyError:
            raise KeyError(
                f"Key '{name}' not found in '{self.__class__.__name__}'. "
                f"Choices are: {', '.join(sorted(self.form_classes.keys()))}."
            )

    @property
    def forms(self) -> dict[str, FormLike]:
        if not self._forms_cache:
            for name in self.form_classes:
                self._forms_cache[name] = self.get_form(name)
        return self._forms_cache

    @classmethod
    def get_default_prefix(cls):
        return "multiform"

    def get_form(self, name):
        try:
            form_class = self.form_classes[name]
        except KeyError:
            raise KeyError(
                f"Key '{name}' not found in '{self.__class__.__name__}'. "
                f"Choices are: {', '.join(sorted(self.form_classes.values()))}."
            )
        return self._construct_form(name, form_class, **self.get_form_kwargs(name, form_class))

    def get_form_kwargs(self, name, form_class):
        return self.form_kwargs.get(name, {}).copy()

    def _construct_form(self, name, form_class, **kwargs):
        """Instantiate and return the i-th form instance in a formset."""
        defaults = {
            "auto_id": self.auto_id,
            "prefix": self.add_prefix(name),
            "error_class": self.error_class,
            "renderer": self.renderer,
        }
        if self.is_bound:
            defaults["data"] = self.data
            defaults["files"] = self.files
        if self.initial and (initial := self.initial.get(name)):
            defaults["initial"] = initial

        defaults.update(kwargs)

        if issubclass(form_class, BaseFormSet):
            # renderer is not a constructor argument of formsets
            # It need to be processed differently
            renderer = defaults.pop("renderer", None)
            form = form_class(**defaults)
            if renderer:
                form.renderer = renderer
            return form

        return form_class(**defaults)

    def add_non_field_error(self, form: str | None, error: str | ValidationError):
        if not isinstance(error, ValidationError):
            error = ValidationError(error)

        if hasattr(error, "error_dict"):
            raise TypeError("The `error` argument cannot contains errors for multiple fields.")

        form = form or NON_FIELD_ERRORS

        if form in self.forms and isinstance(self.forms[form], BaseFormSet):
            self.forms[form].non_form_errors().extend(error.error_list)
            self.errors.setdefault(NON_FIELD_ERRORS, {})
            self.errors[NON_FIELD_ERRORS].update({form: self.forms[form].non_form_errors()})
        elif form in self.forms:
            self.forms[form].add_error(None, error)
            self.errors.setdefault(form, self.forms[form].errors)
        elif form == NON_FIELD_ERRORS:
            self.errors.setdefault(NON_FIELD_ERRORS, {})
            self.errors[NON_FIELD_ERRORS].setdefault(
                NON_FIELD_ERRORS,
                self.error_class(error_class="nonfield", renderer=self.renderer),
            )
            self.errors[NON_FIELD_ERRORS][NON_FIELD_ERRORS].extend(error.error_list)
        else:
            raise ValueError(
                f"'form' argument must be a form name present in {self.form_classes.keys()} or None (was {form})"
            )

    def add_prefix(self, name):
        return "%s-%s" % (self.prefix, name)

    def is_valid(self):
        return self.is_bound and not self.errors

    @property
    def errors(self) -> dict[str, ErrorList | dict[str, ErrorList]] | None:
        """Return a list of form.errors for every form in self.forms."""
        if self._errors is None:
            self.full_clean()
        return self._errors

    def full_clean(self):
        self._errors = {}

        if not self.is_bound:  # Stop further processing.
            return

        for name, form in self.forms.items():
            if form.is_valid():
                if not hasattr(self, "cleaned_data"):
                    self.cleaned_data = {}
                self.cleaned_data[name] = form.cleaned_data
            else:
                if form.errors:
                    self._errors[name] = form.errors
                if isinstance(form, BaseFormSet) and form.non_form_errors():
                    self.errors.setdefault(NON_FIELD_ERRORS, {})
                    self.errors[NON_FIELD_ERRORS].update({name: form.non_form_errors()})

        try:
            self.clean()
        except ValidationError as e:
            self.add_non_field_error(None, e)

    def clean(self):
        pass

    @property
    def media(self):
        return reduce(operator.add, (form.media for form in self))


class BaseModelMultiForm(BaseMultiForm, AltersData):
    def __init__(
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        querysets: None | dict[str, QuerySet] = None,
        initial=None,
        error_class=ErrorList,
        form_kwargs=None,
        renderer=None,
    ):
        self.querysets = querysets or {}
        super().__init__(data, files, auto_id, prefix, initial, error_class, form_kwargs, renderer)

    def get_queryset(self, name) -> QuerySet:
        return self.querysets.get(name, None)

    def get_form_kwargs(self, name, form_class):
        kwargs = super().get_form_kwargs(name, form_class)
        queryset = self.get_queryset(name)
        if "queryset" not in kwargs and queryset is not None and issubclass(self.form_classes[name], ModelFormLike):
            kwargs["queryset"] = queryset
        return kwargs

    @property
    def model_forms(self) -> Iterable[Tuple[str, ModelFormLike]]:
        for name, form in self.forms.items():
            if isinstance(form, ModelFormLike):
                yield name, form

    def save(self, commit=True):
        if self.errors:
            raise ValueError(
                ngettext(
                    "The form %s could not be saved because it has errors.",
                    "The forms %s could not be saved because it has errors.",
                    len(self.errors),
                )
                % (list(self.errors.keys())[0] if len(self.errors) == 1 else ", ".join(self.errors.keys())),
            )

        saved_forms = {}

        for name, form in self.model_forms:
            if hasattr(self, f"save_{name}"):
                saved_forms[name] = getattr(self, f"save_{name}")(form=form, commit=commit)
            else:
                saved_forms[name] = form.save(commit)

        return saved_forms

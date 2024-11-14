from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from core.content_types import content_type_str_to_obj


class MultiModelChoiceField(forms.MultipleChoiceField):
    def __init__(self, model_choices, *args, **kwargs):
        choices = []
        for label, queryset in model_choices:
            content_type = ContentType.objects.get_for_model(queryset.model)
            model_choices = [(f"{content_type.id}-{obj.id}", f"{label} : {obj}") for obj in queryset]
            choices.extend(model_choices)
        super().__init__(choices=choices, *args, **kwargs)

    def clean(self, value):
        list_of_objects = []
        for obj_as_str in value:
            try:
                list_of_objects.append(content_type_str_to_obj(obj_as_str))
            except ObjectDoesNotExist:
                raise forms.ValidationError("L'un des objets sélectionnés n'existe pas.")
        return list_of_objects


class DSFRCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    option_template_name = "forms/dsfr_checkbox_option.html"


class DSFRToogle(forms.CheckboxInput):
    template_name = "forms/dsfr_toogle.html"


class DSFRRadioButton(forms.RadioSelect):
    template_name = "forms/dsfr_radio_btn.html"


class DSFRCheckboxInput(forms.CheckboxInput):
    template_name = "forms/dsfr_checkbox.html"

    def __init__(self, *args, **kwargs):
        self.label = kwargs.pop("label", None)
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["label"] = self.label
        return context

from django import forms
from django.contrib.contenttypes.models import ContentType


class MultiModelChoiceField(forms.ChoiceField):
    def __init__(self, model_choices, *args, **kwargs):
        choices = []
        for label, queryset in model_choices:
            content_type = ContentType.objects.get_for_model(queryset.model)
            model_choices = [(f"{content_type.id}-{obj.id}", f"{label}: {obj}") for obj in queryset]
            choices.extend(model_choices)
        super().__init__(choices=choices, *args, **kwargs)

    def clean(self, value):
        content_type_id, object_id = value.split("-")
        content_type = ContentType.objects.get(id=content_type_id)
        model_class = content_type.model_class()
        try:
            return model_class.objects.get(id=object_id)
        except model_class.DoesNotExist:
            raise forms.ValidationError("L'objet sélectionné n'existe pas.")


class DSFRCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    option_template_name = "forms/dsfr_checkbox_option.html"


class DSFRToogle(forms.CheckboxInput):
    template_name = "forms/dsfr_toogle.html"


class DSFRRadioButton(forms.RadioSelect):
    template_name = "forms/dsfr_radio_btn.html"

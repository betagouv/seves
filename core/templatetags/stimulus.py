from django import template
from django.forms import BaseFormSet
from django.forms.formsets import ManagementForm

register = template.Library()


@register.simple_tag
def stimulus_managment_form(
    item: BaseFormSet | ManagementForm, stimulus_controller_identifier="document-formset"
) -> ManagementForm:
    management_form = item if isinstance(item, ManagementForm) else item.management_form

    for bf in management_form:
        bf.field.widget.attrs[f"data-{stimulus_controller_identifier}-target"] = bf.name

    return management_form

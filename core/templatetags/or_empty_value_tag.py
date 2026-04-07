from django import template
from django.utils.safestring import mark_safe

register = template.Library()


EMPTY_PLACEHOLDER = "Vide"


@register.simple_tag
def empty_value_tag():
    return mark_safe(f'<span class="empty-value">{EMPTY_PLACEHOLDER}</span>')


@register.filter
def or_empty_value_tag(value):
    if value in (None, ""):
        return empty_value_tag()
    return value

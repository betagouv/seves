from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def or_empty_value_tag(value):
    if value in (None, ""):
        return mark_safe('<span class="empty-value">Vide</span>')
    return value

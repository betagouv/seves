from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def with_default_value(value):
    if value in (None, ""):
        return mark_safe('<span class="empty-value">Vide</span>')
    return value

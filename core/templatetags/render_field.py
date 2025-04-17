from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_field(field):
    return mark_safe(f"""
        {field.label_tag()}
        {field}
    """)

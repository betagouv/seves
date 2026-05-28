from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_field(field):
    return mark_safe(f"""
        {field.label_tag()}
        {field}
    """)


# Avoid clash with widget_tweaks's render_field
@register.simple_tag
def seves_render_field(field):
    return render_field(field)

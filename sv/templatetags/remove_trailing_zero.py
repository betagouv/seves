from django import template

register = template.Library()


@register.filter(name="remove_trailing_zero")
def remove_trailing_zero(value: float):
    return str(value).rstrip("0").rstrip(".") if value else value

from django import template

register = template.Library()


@register.filter
def contains(value, substring):
    return substring in value

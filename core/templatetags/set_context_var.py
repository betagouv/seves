from typing import MutableMapping

from django import template

register = template.Library()


@register.simple_tag
def set_context_var(target, key, value):
    if isinstance(target, MutableMapping):
        target[key] = value
    else:
        setattr(target, key, value)
    return ""

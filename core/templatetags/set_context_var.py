import re
from typing import Mapping, MutableMapping

from django import template

register = template.Library()


@register.simple_tag
def set_context_var(target, key, value):
    if isinstance(target, MutableMapping):
        target[key] = value
    else:
        setattr(target, key, value)
    return ""


@register.simple_tag
def merge_data_action(target, value):
    if isinstance(target, Mapping):
        result = target.get("data-action", "")
    else:
        result = getattr(target, "data-action", "")

    result = re.split(r"\s+", result) + [value]
    set_context_var(target, "data-action", " ".join(result).strip())
    return ""

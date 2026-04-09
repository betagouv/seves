from django import template
from django.template import Context
from django.template.base import Variable
from django.template.defaultfilters import pluralize
from django.utils.crypto import get_random_string
from django.utils.text import format_lazy

register = template.Library()


def format_variable(item, field=None):
    var = f"item.{field}" if field else "item"
    return Variable(var).resolve(Context({"item": item}))


@register.inclusion_tag("core/templatetags/and_more_ellipsis_tooltip.html")
def and_more_ellipsis_tooltip(items, *, tooltip_id=None, tooltip_prefix=None, tooltip_prefix_plural=None, field=None):
    if len(items) == 0:
        return {"head": None}

    head, *rest = list(items)
    tooltip_id = tooltip_id or f"tooltip-{get_random_string(6, 'abcdefghijklmnopqrstuvwxyz0123456789')}"

    tooltip_prefix = (
        tooltip_prefix_plural
        if tooltip_prefix_plural and len(rest) > 1
        else format_lazy(tooltip_prefix or "", plural=pluralize(len(rest)))
    )

    return {
        "head": format_variable(head, field) if head else None,
        "rest": [format_variable(it, field) for it in rest],
        "tooltip_id": tooltip_id,
        "tooltip_prefix": tooltip_prefix,
    }

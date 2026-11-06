from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))


@register.filter
def get_bound_field(form, key):
    return form[str(key)]

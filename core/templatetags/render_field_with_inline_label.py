from django import template

register = template.Library()


@register.inclusion_tag("core/templatetags/inline_radio_snippet.html")
def dsfr_inline_radio_field(field) -> dict:
    if field == "":
        raise AttributeError("Invalid form field name in dsfr_form_field.")

    return {"field": field}

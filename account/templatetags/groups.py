from django import template

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    return group_name in [group.name for group in user.groups.all()]

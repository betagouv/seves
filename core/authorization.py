from core.constants import Domains


def has_needed_group(object, user):
    needed_group = Domains.group_for_value(object._meta.app_label)
    if needed_group and needed_group not in [g.name for g in user.groups.all()]:
        return False
    return True

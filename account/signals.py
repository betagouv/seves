from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

User = get_user_model()


@receiver(pre_save, sender=User)
def set_new_user_inactive(sender, instance, **kwargs):
    if instance._state.adding is True and settings.USERS_NOT_ACTIVE_BY_DEFAULT is True:
        instance.is_active = False


@receiver(post_save, sender=User)
def set_user_groups(sender, instance, **kwargs):
    if settings.USERS_DEFAULT_GROUPS:
        groups = Group.objects.filter(name__in=settings.USERS_DEFAULT_GROUPS)
        instance.groups.add(*[g.id for g in groups])

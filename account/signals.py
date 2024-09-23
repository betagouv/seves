from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import pre_save

User = get_user_model()


@receiver(pre_save, sender=User)
def set_new_user_inactive(sender, instance, **kwargs):
    if instance._state.adding is True:
        instance.is_active = False

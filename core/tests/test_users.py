from django.contrib.auth.models import Group
import pytest

from core.factories import UserFactory


@pytest.mark.django_db
def test_users_are_not_active_per_default():
    user = UserFactory()
    assert user.is_active is False


@pytest.mark.django_db
def test_users_can_be_active_using_setting(settings):
    settings.USERS_NOT_ACTIVE_BY_DEFAULT = False
    user = UserFactory()
    assert user.is_active is True


@pytest.mark.django_db
def test_users_can_have_groups_using_setting(settings):
    group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    settings.USERS_DEFAULT_GROUPS = [settings.SV_GROUP]
    user = UserFactory()
    assert user.is_active is False
    assert user.groups.get() == group

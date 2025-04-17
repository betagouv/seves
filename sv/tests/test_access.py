import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from unittest.mock import MagicMock
from core.factories import UserFactory
from django.test import RequestFactory

from seves import settings
from seves.middlewares import LoginAndGroupRequiredMiddleware


@pytest.mark.django_db
@pytest.mark.disable_mocked_authentification_user
def test_sv_pages_needs_to_be_in_sv_group_to_be_accessed():
    user = UserFactory()
    user.is_active = True
    user.save()

    request = RequestFactory().get(reverse("sv:evenement-liste"))
    request.user = user

    get_response = MagicMock()
    middleware = LoginAndGroupRequiredMiddleware(get_response)
    with pytest.raises(PermissionDenied):
        middleware.__call__(request)


@pytest.mark.django_db
@pytest.mark.disable_mocked_authentification_user
def test_ok_sv_pages_needs_to_be_in_sv_group_to_be_accessed():
    user = UserFactory()
    user.is_active = True
    user.save()
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    user.groups.add(sv_group)

    request = RequestFactory().get(reverse("sv:evenement-liste"))
    request.user = user

    get_response = MagicMock()
    middleware = LoginAndGroupRequiredMiddleware(get_response)
    middleware.__call__(request)

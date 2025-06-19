import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.urls import reverse
from unittest.mock import MagicMock
from core.factories import UserFactory
from django.test import RequestFactory

from seves import settings
from seves.middlewares import LoginAndGroupRequiredMiddleware, HomeRedirectMiddleware


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


@pytest.mark.django_db
def test_redirect_to_sv_if_preferred_domain_when_user_in_both_groups():
    user = UserFactory()
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    user.groups.add(ssa_group, sv_group)

    request = RequestFactory().get("/")
    request.user = user
    request.COOKIES["preferred_domain"] = "sv"

    response = HomeRedirectMiddleware(lambda request: HttpResponse("OK"))(request)
    assert response.status_code == 302
    assert response.url == reverse("sv:evenement-liste")


@pytest.mark.django_db
def test_redirect_to_ssa_per_default():
    user = UserFactory()
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    user.groups.add(ssa_group, sv_group)

    request = RequestFactory().get("/")
    request.user = user

    response = HomeRedirectMiddleware(lambda request: HttpResponse("OK"))(request)
    assert response.status_code == 302
    assert response.url == reverse("ssa:evenement-produit-liste")

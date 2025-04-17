import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from playwright.sync_api import expect
from django.urls import reverse

from core.factories import AgentFactory

User = get_user_model()


@pytest.mark.django_db
def test_need_group_to_add_permission(live_server, page, mocked_authentification_user):
    response = page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    assert response.status == 403


@pytest.mark.django_db
def test_user_can_see_navigation_without_group(live_server, page, mocked_authentification_user):
    page.goto(f"{live_server.url}")
    page.get_by_role("button", name="test@example.com").click()
    page.wait_for_timeout(200)
    expect(page.get_by_text("Gestion des droits d'accès")).not_to_be_visible()


@pytest.mark.django_db
def test_can_add_permissions(live_server, page, mocked_authentification_user):
    Group.objects.get_or_create(name=settings.SV_GROUP)
    structure = mocked_authentification_user.agent.structure
    group, _ = Group.objects.get_or_create(name="access_admin")
    mocked_authentification_user.groups.add(group)
    AgentFactory(structure=structure, prenom="Ian", nom="Gillan")
    AgentFactory(structure=structure, prenom="Ritchie", nom="Blackmore")
    AgentFactory(structure=structure, prenom="Ian", nom="Paice")
    AgentFactory(prenom="John", nom="Lennon")
    User.objects.exclude(pk=mocked_authentification_user.pk).update(is_active=False)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")

    expect(page.get_by_text("Gillan Ian")).to_be_visible()
    expect(page.get_by_text("Blackmore Ritchie")).to_be_visible()
    expect(page.get_by_text("Paice Ian")).to_be_visible()
    expect(page.get_by_text("Paice Lennon")).not_to_be_visible()

    page.get_by_text("Gillan Ian").click()
    page.get_by_text("Paice Ian").click()

    page.get_by_role("button", name="Enregistrer les modifications").click()

    assert User.objects.filter(agent__prenom="Ian", is_active=True).count() == 2
    assert User.objects.get(agent__nom="Blackmore").is_active is False
    assert User.objects.get(agent__nom="Lennon").is_active is False


@pytest.mark.django_db
def test_can_remove_permissions(live_server, page, mocked_authentification_user):
    Group.objects.get_or_create(name=settings.SV_GROUP)
    structure = mocked_authentification_user.agent.structure
    group, _ = Group.objects.get_or_create(name="access_admin")
    mocked_authentification_user.groups.add(group)
    AgentFactory(structure=structure, prenom="Ian", nom="Gillan")
    AgentFactory(structure=structure, prenom="Ritchie", nom="Blackmore")
    User.objects.exclude(pk=mocked_authentification_user.pk).update(is_active=True)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.get_by_text("Gillan Ian").click()
    page.get_by_text("Blackmore Ritchie").click()

    page.get_by_role("button", name="Enregistrer les modifications").click()

    assert User.objects.get(agent__nom="Blackmore").is_active is False
    assert User.objects.get(agent__nom="Gillan").is_active is False


@pytest.mark.django_db
def test_cant_remove_permissions_for_myself(live_server, page, mocked_authentification_user):
    group, _ = Group.objects.get_or_create(name="access_admin")
    mocked_authentification_user.groups.add(group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    expect(page.get_by_text("Doe John")).not_to_be_visible()

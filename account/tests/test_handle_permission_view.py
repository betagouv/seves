import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from playwright.sync_api import expect
from model_bakery import baker
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_need_group_to_add_permission(live_server, page, mocked_authentification_user):
    response = page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    assert response.status == 403


@pytest.mark.django_db
def test_can_add_permissions(live_server, page, mocked_authentification_user):
    structure = mocked_authentification_user.agent.structure
    group = Group.objects.create(name="access_admin")
    mocked_authentification_user.groups.add(group)
    baker.make(User, agent__structure=structure, agent__prenom="Ian", agent__nom="Gillan")
    baker.make(User, agent__structure=structure, agent__prenom="Ritchie", agent__nom="Blackmore")
    baker.make(User, agent__structure=structure, agent__prenom="Ian", agent__nom="Paice")
    baker.make(User, agent__nom="Lennon", agent__prenom="John")
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
    structure = mocked_authentification_user.agent.structure
    group = Group.objects.create(name="access_admin")
    mocked_authentification_user.groups.add(group)
    baker.make(User, agent__structure=structure, agent__prenom="Ian", agent__nom="Gillan")
    baker.make(User, agent__structure=structure, agent__prenom="Ritchie", agent__nom="Blackmore")
    User.objects.exclude(pk=mocked_authentification_user.pk).update(is_active=True)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.get_by_text("Gillan Ian").click()
    page.get_by_text("Blackmore Ritchie").click()

    page.get_by_role("button", name="Enregistrer les modifications").click()

    assert User.objects.get(agent__nom="Blackmore").is_active is False
    assert User.objects.get(agent__nom="Gillan").is_active is False


@pytest.mark.django_db
def test_cant_remove_permissions_for_myself(live_server, page, mocked_authentification_user):
    group = Group.objects.create(name="access_admin")
    mocked_authentification_user.groups.add(group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    expect(page.get_by_text("Doe John")).not_to_be_visible()

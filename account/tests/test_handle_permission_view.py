import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from playwright.sync_api import expect
from django.urls import reverse

from core.factories import AgentFactory
from seves.settings import CAN_GIVE_ACCESS_GROUP

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
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure = mocked_authentification_user.agent.structure
    mocked_authentification_user.groups.add(access_admin_group)
    agent_1 = AgentFactory(structure=structure, prenom="Ian", nom="Gillan")
    agent_2 = AgentFactory(structure=structure, prenom="Ian", nom="Paice")
    agent_3 = AgentFactory(structure=structure, prenom="Ritchie", nom="Blackmore")
    agent_4 = AgentFactory(prenom="John", nom="Lennon")
    User.objects.exclude(pk=mocked_authentification_user.pk).update(is_active=False)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")

    expect(page.get_by_text("Gillan Ian")).to_be_visible()
    expect(page.get_by_text("Blackmore Ritchie")).to_be_visible()
    expect(page.get_by_text("Paice Ian")).to_be_visible()
    expect(page.get_by_text("Lennon John")).not_to_be_visible()

    page.locator(f"input[id='sv_{agent_1.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{agent_2.pk}']").click(force=True)
    page.locator(f"input[id='sv_{agent_3.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{agent_3.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expect(page.get_by_role("heading", name="Modification de droits")).to_be_visible()

    agent_1.refresh_from_db()
    agent_2.refresh_from_db()
    agent_3.refresh_from_db()
    agent_4.refresh_from_db()

    assert set(agent_1.user.groups.all()) == {sv_group}
    assert set(agent_2.user.groups.all()) == {ssa_group}
    assert set(agent_3.user.groups.all()) == {sv_group, ssa_group}
    assert agent_4.user.groups.count() == 0

    assert agent_1.user.is_active is True
    assert agent_2.user.is_active is True
    assert agent_3.user.is_active is True
    assert agent_4.user.is_active is False


@pytest.mark.django_db
def test_can_remove_permissions(live_server, page, mocked_authentification_user):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure = mocked_authentification_user.agent.structure
    mocked_authentification_user.groups.add(access_admin_group)
    agent_1 = AgentFactory(structure=structure, prenom="Ian", nom="Gillan")
    agent_2 = AgentFactory(structure=structure, prenom="Ian", nom="Paice")
    agent_3 = AgentFactory(structure=structure, prenom="Ritchie", nom="Blackmore")
    agent_4 = AgentFactory(structure=structure, prenom="John", nom="Lennon")
    agent_1.user.groups.add(sv_group)
    agent_2.user.groups.add(ssa_group)
    agent_3.user.groups.add(sv_group, ssa_group)
    agent_4.user.groups.add(sv_group, ssa_group)
    User.objects.exclude(pk=mocked_authentification_user.pk).update(is_active=True)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.locator(f"input[id='sv_{agent_1.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{agent_2.pk}']").click(force=True)
    page.locator(f"input[id='sv_{agent_3.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{agent_3.pk}']").click(force=True)
    page.locator(f"input[id='sv_{agent_4.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expect(page.get_by_role("heading", name="Modification de droits")).to_be_visible()

    agent_1.refresh_from_db()
    agent_2.refresh_from_db()
    agent_3.refresh_from_db()
    agent_4.refresh_from_db()

    assert set(agent_1.user.groups.all()) == set()
    assert set(agent_2.user.groups.all()) == set()
    assert set(agent_3.user.groups.all()) == set()
    assert set(agent_4.user.groups.all()) == {ssa_group}

    assert agent_1.user.is_active is False
    assert agent_2.user.is_active is False
    assert agent_3.user.is_active is False
    assert agent_4.user.is_active is True


@pytest.mark.django_db
def test_cant_remove_permissions_for_myself(live_server, page, mocked_authentification_user):
    group, _ = Group.objects.get_or_create(name="access_admin")
    mocked_authentification_user.groups.add(group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    expect(page.get_by_text("Doe John")).not_to_be_visible()

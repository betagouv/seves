import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from playwright.sync_api import expect
from django.urls import reverse

from core.factories import AgentFactory
from seves.settings import CAN_GIVE_ACCESS_GROUP
from core.factories import ContactAgentFactory

User = get_user_model()


@pytest.mark.django_db
def test_need_group_to_add_permission(live_server, page, mocked_authentification_user):
    response = page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    assert response.status == 403


@pytest.mark.django_db
def test_user_cant_see_navigation_without_group(live_server, page, mocked_authentification_user):
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
    mocked_authentification_user.groups.add(access_admin_group, sv_group, ssa_group)
    contact_agent_1 = ContactAgentFactory(agent__structure=structure)
    contact_agent_2 = ContactAgentFactory(agent__structure=structure)
    contact_agent_3 = ContactAgentFactory(agent__structure=structure)
    contact_agent_4 = ContactAgentFactory()
    User.objects.exclude(pk=mocked_authentification_user.pk).update(is_active=False)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")

    expect(page.get_by_text(str(contact_agent_1))).to_be_visible()
    expect(page.get_by_text(str(contact_agent_2))).to_be_visible()
    expect(page.get_by_text(str(contact_agent_3))).to_be_visible()
    expect(page.get_by_text(str(contact_agent_4))).not_to_be_visible()

    page.locator(f"input[id='sv_{contact_agent_1.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{contact_agent_2.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='sv_{contact_agent_3.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{contact_agent_3.agent.user.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expect(page.get_by_role("heading", name="Modification de droits")).to_be_visible()

    contact_agent_1.refresh_from_db()
    contact_agent_2.refresh_from_db()
    contact_agent_3.refresh_from_db()
    contact_agent_4.refresh_from_db()

    assert set(contact_agent_1.agent.user.groups.all()) == {sv_group}
    assert set(contact_agent_2.agent.user.groups.all()) == {ssa_group}
    assert set(contact_agent_3.agent.user.groups.all()) == {sv_group, ssa_group}
    assert contact_agent_4.agent.user.groups.count() == 0

    assert contact_agent_1.agent.user.is_active is True
    assert contact_agent_2.agent.user.is_active is True
    assert contact_agent_3.agent.user.is_active is True
    assert contact_agent_4.agent.user.is_active is False


@pytest.mark.django_db
def test_can_remove_permissions(live_server, page, mocked_authentification_user):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure = mocked_authentification_user.agent.structure
    mocked_authentification_user.groups.add(access_admin_group, sv_group, ssa_group)
    contact_agent_1 = ContactAgentFactory(agent__structure=structure)
    contact_agent_2 = ContactAgentFactory(agent__structure=structure)
    contact_agent_3 = ContactAgentFactory(agent__structure=structure)
    contact_agent_4 = ContactAgentFactory(agent__structure=structure)
    contact_agent_1.agent.user.groups.add(sv_group)
    contact_agent_2.agent.user.groups.add(ssa_group)
    contact_agent_3.agent.user.groups.add(sv_group, ssa_group)
    contact_agent_4.agent.user.groups.add(sv_group, ssa_group)
    User.objects.exclude(pk=mocked_authentification_user.pk).update(is_active=True)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    page.locator(f"input[id='sv_{contact_agent_1.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{contact_agent_2.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='sv_{contact_agent_3.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='ssa_{contact_agent_3.agent.user.pk}']").click(force=True)
    page.locator(f"input[id='sv_{contact_agent_4.agent.user.pk}']").click(force=True)
    page.get_by_role("button", name="Enregistrer les modifications").click()

    expect(page.get_by_role("heading", name="Modification de droits")).to_be_visible()

    contact_agent_1.refresh_from_db()
    contact_agent_2.refresh_from_db()
    contact_agent_3.refresh_from_db()
    contact_agent_4.refresh_from_db()

    assert set(contact_agent_1.agent.user.groups.all()) == set()
    assert set(contact_agent_2.agent.user.groups.all()) == set()
    assert set(contact_agent_3.agent.user.groups.all()) == set()
    assert set(contact_agent_4.agent.user.groups.all()) == {ssa_group}

    assert contact_agent_1.agent.user.is_active is False
    assert contact_agent_2.agent.user.is_active is False
    assert contact_agent_3.agent.user.is_active is False
    assert contact_agent_4.agent.user.is_active is True


@pytest.mark.django_db
def test_cant_remove_permissions_for_myself(live_server, page, mocked_authentification_user):
    group, _ = Group.objects.get_or_create(name="access_admin")
    mocked_authentification_user.groups.add(group)

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")
    expect(page.get_by_text("Doe John")).not_to_be_visible()


@pytest.mark.django_db
def test_sv_user_cant_manage_ssa_permissions(live_server, page, mocked_authentification_user):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure = mocked_authentification_user.agent.structure
    mocked_authentification_user.groups.add(access_admin_group, sv_group)
    agent = AgentFactory(structure=structure, prenom="Test", nom="User")

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")

    expect(page.get_by_text("SV")).to_be_visible()
    expect(page.get_by_text("SSA")).not_to_be_visible()
    expect(page.locator(f"input[id='sv_{agent.user.pk}']")).to_be_visible()
    expect(page.locator(f"input[id='ssa_{agent.user.pk}']")).not_to_be_visible()


@pytest.mark.django_db
def test_ssa_user_cant_manage_sv_permissions(live_server, page, mocked_authentification_user):
    Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure = mocked_authentification_user.agent.structure
    mocked_authentification_user.groups.add(access_admin_group, ssa_group)
    agent = AgentFactory(structure=structure, prenom="Test", nom="User")

    page.goto(f"{live_server.url}/{reverse('handle-permissions')}")

    expect(page.get_by_text("SSA")).to_be_visible()
    expect(page.get_by_text("SV")).not_to_be_visible()
    expect(page.locator(f"input[id='ssa_{agent.user.pk}']")).to_be_visible()
    expect(page.locator(f"input[id='sv_{agent.user.pk}']")).not_to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_group_name,permission_to_forge",
    [
        (settings.SV_GROUP, "ssa"),  # SV user trying to forge SSA permissions
        (settings.SSA_GROUP, "sv"),  # SSA user trying to forge SV permissions
    ],
)
def test_users_cant_forge_other_group_permissions(
    client, mocked_authentification_user, user_group_name, permission_to_forge
):
    Group.objects.get_or_create(name=settings.SV_GROUP)
    Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    user_group = Group.objects.get(name=user_group_name)
    mocked_authentification_user.groups.add(access_admin_group, user_group)
    agent = AgentFactory(prenom="Test", nom="User")
    assert agent.user.groups.count() == 0
    assert agent.user.is_active is False

    client.post(
        reverse("handle-permissions"),
        data={f"{permission_to_forge}_{agent.user.pk}": "on", "next": reverse("sv:evenement-liste")},
        follow=True,
    )

    agent.refresh_from_db()
    assert agent.user.groups.count() == 0
    assert agent.user.is_active is False

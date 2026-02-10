from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from playwright.sync_api import expect
import pytest

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import AgentFactory, ContactAgentFactory
from core.models import Structure
from seves.settings import CAN_GIVE_ACCESS_GROUP, SSA_GROUP

User = get_user_model()


@pytest.mark.django_db
def test_need_to_be_mus_to_add_permission(live_server, page, mocked_authentification_user):
    response = page.goto(f"{live_server.url}/{reverse('handle-admins')}")
    assert response.status == 403


@pytest.mark.django_db
def test_user_cant_see_navigation_without_group(live_server, page, mocked_authentification_user, choice_js_get_values):
    page.goto(f"{live_server.url}")
    page.get_by_role("button", name="test@example.com").click()
    page.wait_for_timeout(200)
    expect(page.get_by_text("Gestion des administrateurs")).not_to_be_visible()


@pytest.mark.django_db
def test_can_add_admin_permissions(
    live_server, page, mocked_authentification_user, choice_js_get_all_values, choice_js_fill
):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE)
    mocked_authentification_user.agent.structure = structure

    agent_already_admin = AgentFactory(with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP])
    contact_agent_will_be_admin = ContactAgentFactory()
    agent_will_be_admin = contact_agent_will_be_admin.agent

    page.goto(f"{live_server.url}/{reverse('handle-admins')}")
    expect(page.locator("table").get_by_text(agent_already_admin.agent_with_structure, exact=True)).to_be_visible()
    assert agent_already_admin.agent_with_structure not in choice_js_get_all_values(page, ".choices")

    choice_js_fill(page, ".choices", agent_will_be_admin.agent_with_structure, agent_will_be_admin.agent_with_structure)
    page.get_by_label("SSA").check(force=True)
    page.get_by_role("button", name="Accorder le rôle administrateur").click()
    page.get_by_role("button", name="Confirmer le rôle d’administrateur").click()
    expect(page.get_by_text("Le rôle administrateur a été accordé")).to_be_visible()

    expect(page.locator("table").get_by_text(agent_will_be_admin.agent_with_structure, exact=True)).to_be_visible()
    assert agent_will_be_admin.agent_with_structure not in choice_js_get_all_values(page, ".choices")

    agent_will_be_admin.refresh_from_db()
    assert agent_will_be_admin.user.is_active is True
    assert set(agent_will_be_admin.user.groups.values_list("name", flat=True)) == {CAN_GIVE_ACCESS_GROUP, SSA_GROUP}


@pytest.mark.django_db
def test_can_remove_admin_permissions(live_server, page, mocked_authentification_user):
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE)
    mocked_authentification_user.agent.structure = structure
    agent_already_admin = AgentFactory(
        with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP, settings.SSA_GROUP]
    )

    page.goto(f"{live_server.url}/{reverse('handle-admins')}")
    expect(page.locator("table").get_by_text(agent_already_admin.agent_with_structure, exact=True)).to_be_visible()

    page.get_by_role("link", name="Révoquer le rôle d’administrateur").click()
    page.get_by_role("button", name="Confirmer la révocation").click()
    expect(page.get_by_text("Le rôle administrateur a été révoqué")).to_be_visible()
    expect(page.locator("table").get_by_text(agent_already_admin.agent_with_structure, exact=True)).not_to_be_visible()

    agent_already_admin.refresh_from_db()
    assert agent_already_admin.user.is_active is True
    assert set(agent_already_admin.user.groups.values_list("name", flat=True)) == {SSA_GROUP}

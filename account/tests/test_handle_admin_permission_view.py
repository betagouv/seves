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
    assert agent_already_admin.agent_with_structure in choice_js_get_all_values(page, ".choices")

    choice_js_fill(page, ".choices", agent_will_be_admin.agent_with_structure, agent_will_be_admin.agent_with_structure)
    page.locator(".white-container").get_by_text("Alim", exact=True).check()
    page.get_by_role("button", name="Accorder le rôle administrateur").click()
    expect(page.locator("#fr-modal-add-user")).to_be_visible()
    page.get_by_role("button", name="Confirmer le rôle d’administrateur").click()
    expect(page.get_by_text("Le rôle administrateur a été accordé")).to_be_visible()

    expect(page.locator("table").get_by_text(agent_will_be_admin.agent_with_structure, exact=True)).to_be_visible()
    assert agent_will_be_admin.agent_with_structure in choice_js_get_all_values(page, ".choices")

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


@pytest.mark.django_db
def test_performances_admin_page_scales(client, mocked_authentification_user, django_assert_num_queries):
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE)
    mocked_authentification_user.agent.structure = structure
    AgentFactory(with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP, settings.SSA_GROUP])

    with django_assert_num_queries(8):
        response = client.get(reverse("handle-admins"))
        assert response.status_code == 200

    AgentFactory(with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP, settings.SSA_GROUP])
    AgentFactory(with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP, settings.SSA_GROUP])
    AgentFactory(with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP, settings.SSA_GROUP])

    with django_assert_num_queries(8):
        response = client.get(reverse("handle-admins"))
        assert response.status_code == 200


@pytest.mark.django_db
def test_can_add_admin_permissions_to_user_with_existing_permissions(
    live_server, page, mocked_authentification_user, choice_js_get_all_values, choice_js_fill
):
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE)
    mocked_authentification_user.agent.structure = structure

    agent_already_admin = AgentFactory(
        with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP, settings.SV_GROUP]
    )
    ContactAgentFactory(agent=agent_already_admin)

    page.goto(f"{live_server.url}/{reverse('handle-admins')}")
    expect(page.locator("table").get_by_text(agent_already_admin.agent_with_structure, exact=True)).to_be_visible()

    choice_js_fill(page, ".choices", agent_already_admin.agent_with_structure, agent_already_admin.agent_with_structure)
    page.locator(".white-container").get_by_text("Alim", exact=True).check()
    page.locator(".white-container").get_by_text("SV", exact=True).uncheck()
    page.get_by_role("button", name="Accorder le rôle administrateur").click()
    expect(page.locator("#fr-modal-add-user")).to_be_visible()
    page.get_by_role("button", name="Confirmer le rôle d’administrateur").click()
    expect(page.get_by_text("Le rôle administrateur a été accordé")).to_be_visible()

    expect(page.locator("table").get_by_text(agent_already_admin.agent_with_structure, exact=True)).to_be_visible()
    assert agent_already_admin.agent_with_structure in choice_js_get_all_values(page, ".choices")

    agent_already_admin.refresh_from_db()
    assert agent_already_admin.user.is_active is True
    assert set(agent_already_admin.user.groups.values_list("name", flat=True)) == {CAN_GIVE_ACCESS_GROUP, SSA_GROUP}


@pytest.mark.django_db
def test_can_filter_table_on_structure(live_server, page, mocked_authentification_user, choice_js_fill):
    access_admin_group, _ = Group.objects.get_or_create(name=CAN_GIVE_ACCESS_GROUP)
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE)
    mocked_authentification_user.agent.structure = structure

    agent_already_admin_1 = AgentFactory(
        with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP], structure__libelle="DDPP1"
    )
    agent_already_admin_2 = AgentFactory(
        with_active_user__with_groups=[settings.CAN_GIVE_ACCESS_GROUP], structure__libelle="DDPP2"
    )

    page.goto(f"{live_server.url}/{reverse('handle-admins')}")
    expect(page.locator("table").get_by_text(agent_already_admin_1.agent_with_structure, exact=True)).to_be_visible()
    expect(page.locator("table").get_by_text(agent_already_admin_2.agent_with_structure, exact=True)).to_be_visible()

    choice_js_fill(page, page.locator(".fr-table .choices"), "DDPP1", "DDPP1")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.locator("table").get_by_text(agent_already_admin_1.agent_with_structure, exact=True)).to_be_visible()
    expect(
        page.locator("table").get_by_text(agent_already_admin_2.agent_with_structure, exact=True)
    ).not_to_be_visible()

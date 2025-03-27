import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect

from core.constants import MUS_STRUCTURE, BSV_STRUCTURE, AC_STRUCTURE
from core.factories import StructureFactory, ContactAgentFactory, ContactStructureFactory
from core.models import Structure, Visibilite
from sv.factories import EvenementFactory
from sv.models import Evenement


def test_users_cant_update_visibilite(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_text("Modifier la visibilité")).not_to_be_visible()


@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_users_from_ac_can_update_visibilite(live_server, page: Page, mocked_authentification_user, structure_ac):
    evenement = EvenementFactory()
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=structure_ac)
    ContactStructureFactory(structure=structure)
    mocked_authentification_user.agent.structure = structure
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.locator("#action-1").get_by_text("Modifier la visibilité").click()

    expect(page.get_by_label("Local")).to_be_checked()
    page.get_by_label("National").click(force=True)
    page.get_by_role("button", name="Valider").click()

    expect(page.get_by_text("La visibilité de l'évenement a bien été modifiée.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.visibilite == Visibilite.NATIONALE


@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_cant_update_visibilite_when_draft(live_server, page: Page, mocked_authentification_user, structure_ac):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=structure_ac)
    ContactStructureFactory(structure=structure)
    mocked_authentification_user.agent.structure = structure
    mocked_authentification_user.agent.save()
    evenement.createur = mocked_authentification_user.agent.structure
    evenement.save()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.locator("#action-1").get_by_text("Modifier la visibilité")).not_to_be_visible()


@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_users_from_ac_can_update_visibilite_backward(
    live_server, page: Page, mocked_authentification_user, structure_ac
):
    evenement = EvenementFactory(visibilite=Visibilite.NATIONALE)
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=structure_ac)
    ContactStructureFactory(structure=structure)
    mocked_authentification_user.agent.structure = structure
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.locator("#action-1").get_by_text("Modifier la visibilité").click()

    expect(page.get_by_label("National")).to_be_checked()
    page.get_by_label("Local").click(force=True)
    page.get_by_role("button", name="Valider").click()

    expect(page.get_by_text("La visibilité de l'évenement a bien été modifiée.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.visibilite == Visibilite.LOCALE


def test_user_not_from_ac_cant_load_structure_add_page(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementFactory()
    url = reverse("sv:structure-add-visibilite", kwargs={"pk": evenement.pk})
    response = page.goto(f"{live_server.url}{url}")

    assert response.status == 403


def test_existing_allowed_structures_are_selected_on_structure_add_page(
    live_server, page: Page, mocked_authentification_user
):
    evenement = EvenementFactory()
    selected_structure = StructureFactory()
    agent_contact = ContactAgentFactory(agent__structure=selected_structure)
    agent_contact.agent.user.is_active = True
    agent_contact.agent.user.save()
    not_selected_structure = StructureFactory()
    agent_contact = ContactAgentFactory(agent__structure=not_selected_structure)
    agent_contact.agent.user.is_active = True
    agent_contact.agent.user.save()
    evenement.allowed_structures.set([selected_structure])

    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE
    )
    mocked_authentification_user.agent.save()

    url = reverse("sv:structure-add-visibilite", kwargs={"pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    expect(page.get_by_label(str(selected_structure))).to_be_checked()
    expect(page.get_by_label(str(not_selected_structure))).not_to_be_checked()


def test_user_from_ac_can_change_to_limitee_and_pick_structure(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementFactory()
    structure_1 = StructureFactory()
    agent_contact = ContactAgentFactory(agent__structure=structure_1)
    agent_contact.agent.user.is_active = True
    agent_contact.agent.user.save()
    structure_2 = StructureFactory()
    agent_contact = ContactAgentFactory(agent__structure=structure_2)
    agent_contact.agent.user.is_active = True
    agent_contact.agent.user.save()

    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE
    )
    mocked_authentification_user.agent.save()

    assert evenement.visibilite == Visibilite.LOCALE
    url = reverse("sv:structure-add-visibilite", kwargs={"pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")
    page.get_by_label(str(structure_1)).click(force=True)
    page.get_by_role("button", name="Valider").click()

    evenement.refresh_from_db()
    assert evenement.allowed_structures.get() == structure_1
    assert evenement.visibilite == Visibilite.LIMITEE


def test_ac_and_creator_structures_are_checked_and_disabled(live_server, page: Page, mocked_authentification_user):
    # Créer les structures AC (MUS et BSV) et ajoute des contacts actifs
    mus_structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, defaults={"libelle": MUS_STRUCTURE}
    )
    mus_contact = ContactAgentFactory(agent__structure=mus_structure)
    mus_contact.agent.user.is_active = True
    mus_contact.agent.user.save()
    bsv_structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=BSV_STRUCTURE, defaults={"libelle": BSV_STRUCTURE}
    )
    bsv_contact = ContactAgentFactory(agent__structure=bsv_structure)
    bsv_contact.agent.user.is_active = True
    bsv_contact.agent.user.save()

    # Créer une structure créatrice
    creator_structure = StructureFactory()
    creator_contact = ContactAgentFactory(agent__structure=creator_structure)
    creator_contact.agent.user.is_active = True
    creator_contact.agent.user.save()

    # Créer d'autres structures non-AC pour la comparaison
    other_structure = StructureFactory()
    agent_contact = ContactAgentFactory(agent__structure=other_structure)
    agent_contact.agent.user.is_active = True
    agent_contact.agent.user.save()

    # Configurer l'utilisateur authentifié comme membre de MUS
    mocked_authentification_user.agent.structure = mus_structure
    mocked_authentification_user.agent.save()

    evenement = EvenementFactory(createur=creator_structure)

    url = reverse("sv:structure-add-visibilite", kwargs={"pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    # Vérifier que les structures AC sont cochées et désactivées
    mus_checkbox = page.get_by_label(str(mus_structure))
    bsv_checkbox = page.get_by_label(str(bsv_structure))
    expect(mus_checkbox).to_be_checked()
    expect(mus_checkbox).to_be_disabled()
    expect(bsv_checkbox).to_be_checked()
    expect(bsv_checkbox).to_be_disabled()

    # Vérifier que la structure créatrice est cochée et désactivée
    creator_checkbox = page.get_by_label(str(creator_structure))
    expect(creator_checkbox).to_be_checked()
    expect(creator_checkbox).to_be_disabled()

    # Vérifier que les autres structures ne sont ni cochées ni désactivées
    other_checkbox = page.get_by_label(str(other_structure))
    expect(other_checkbox).not_to_be_checked()
    expect(other_checkbox).not_to_be_disabled()

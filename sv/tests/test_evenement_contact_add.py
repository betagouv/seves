import pytest
from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import expect, Page
from django.urls import reverse

from core.constants import MUS_STRUCTURE
from core.factories import ContactAgentFactory, ContactStructureFactory, StructureFactory
from core.models import Contact
from sv.factories import EvenementFactory
from sv.models import Evenement


@pytest.fixture
def contact(db):
    return ContactAgentFactory(with_active_agent=True)


@pytest.fixture
def contacts(db):
    ContactAgentFactory.create_batch(2)

    # création de la structure MUS et de deux contacts de type Agent associés
    structure = StructureFactory(libelle=MUS_STRUCTURE)
    return ContactAgentFactory.create_batch(2, agent__structure=structure, with_active_agent=True)


def test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill):
    contact = ContactAgentFactory(with_active_agent=True)
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    choice_js_fill(page, "#add-contact-agent-form .choices", contact.agent.nom, contact.display_with_agent_unit)
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()
    page.get_by_role("tab", name="Contacts").click()

    expect(page.get_by_text("L'agent a été ajouté avec succès.")).to_be_visible()
    expect(page.get_by_test_id("contacts-agents")).to_be_visible()
    assert page.get_by_test_id("contacts-agents").count() == 1
    assert Evenement.objects.filter(pk=evenement.pk, contacts=contact).exists()


def test_cant_add_inactive_agent_to_an_evenement(live_server, page, choice_js_cant_pick):
    contact = ContactAgentFactory()
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    choice_js_cant_pick(page, "#add-contact-agent-form .choices", contact.agent.nom, contact.display_with_agent_unit)


def test_cant_add_inactive_structure_to_an_evenement(live_server, page, choice_js_cant_pick):
    contact = ContactStructureFactory(email="")
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    choice_js_cant_pick(page, "#add-contact-structure-form .choices", str(contact), str(contact))


def test_add_multiple_contacts_agents_to_an_evenement(live_server, page, choice_js_fill):
    contact_agent_1, contact_agent_2 = ContactAgentFactory.create_batch(2, with_active_agent=True)
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    choice_js_fill(
        page, "#add-contact-agent-form .choices", contact_agent_1.agent.nom, contact_agent_1.display_with_agent_unit
    )
    page.get_by_role("tab", name="Contacts").click()
    page.wait_for_timeout(1000)
    choice_js_fill(
        page, "#add-contact-agent-form .choices", contact_agent_2.agent.nom, contact_agent_2.display_with_agent_unit
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    expect(page.get_by_text("Les 2 agents ont été ajoutés avec succès.")).to_be_visible()
    page.get_by_role("tab", name="Contacts").click()
    assert page.get_by_test_id("contacts-agents").count() == 2
    expect(
        page.get_by_test_id("contacts-agents").get_by_text(
            f"{contact_agent_1.agent.nom} {contact_agent_1.agent.prenom}", exact=True
        )
    ).to_be_visible()
    expect(
        page.get_by_test_id("contacts-agents").get_by_text(
            f"{contact_agent_2.agent.nom} {contact_agent_2.agent.prenom}", exact=True
        )
    ).to_be_visible()


def test_cant_add_contact_agent_if_evenement_brouillon(client, contact):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    response = client.post(
        reverse("agent-add"),
        data={
            "contacts_agents": [contact.id],
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "content_id": evenement.id,
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_cant_delete_contact_if_evenement_brouillon(client, contact):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    evenement.contacts.set([contact])

    response = client.post(
        reverse("contact-delete"),
        data={
            "content_type_pk": ContentType.objects.get_for_model(evenement).id,
            "fiche_pk": evenement.id,
            "pk": contact.id,
            "next": evenement.get_absolute_url(),
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_add_agent_contact_adds_structure_contact(live_server, page, choice_js_fill):
    """Test que l'ajout d'un contact agent ajoute automatiquement le contact de sa structure"""
    structure_contact = ContactStructureFactory()
    agent_contact = ContactAgentFactory(agent__structure=structure_contact.structure, with_active_agent=True)
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    choice_js_fill(
        page, "#add-contact-agent-form .choices", agent_contact.agent.nom, agent_contact.display_with_agent_unit
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    expect(page.get_by_test_id("contacts-agents").get_by_text(str(agent_contact), exact=True)).to_be_visible()
    expect(
        page.get_by_test_id("contacts-structures").get_by_text(str(agent_contact.agent.structure), exact=True)
    ).to_be_visible()


def test_add_multiple_agent_contacts_adds_structure_contact_once(live_server, page, choice_js_fill):
    """Test que l'ajout de plusieurs contacts agents de la même structure n'ajoute qu'une seule fois le contact structure"""
    structure_contact = ContactStructureFactory()
    contact_agent_1, contact_agent_2 = ContactAgentFactory.create_batch(
        2, agent__structure=structure_contact.structure, with_active_agent=True
    )
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    choice_js_fill(
        page,
        "#add-contact-agent-form",
        contact_agent_1.agent.nom,
        contact_agent_1.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.get_by_role("tab", name="Contacts").click()
    page.wait_for_timeout(1000)
    choice_js_fill(
        page,
        "#add-contact-agent-form",
        contact_agent_2.agent.nom,
        contact_agent_2.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    page.get_by_role("tab", name="Contacts").click()

    agents_section = page.locator("[data-testid='contacts-agents']")
    expect(agents_section.get_by_text(str(contact_agent_1.agent), exact=True)).to_be_visible()
    expect(agents_section.get_by_text(str(contact_agent_2.agent), exact=True)).to_be_visible()

    structures_section = page.locator("[data-testid='contacts-structures']")
    expect(structures_section).to_have_count(1)
    expect(structures_section.get_by_text(str(structure_contact.structure), exact=True)).to_be_visible()


def test_cant_forge_add_contact_structure_on_evenement_i_cant_see(client, mocked_authentification_user):
    evenement = EvenementFactory(createur=StructureFactory())
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
        "contacts_structures": [Contact.objects.get(structure=mocked_authentification_user.agent.structure)],
    }
    response = client.post(reverse("structure-add"), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.contacts.count() == 0


def test_cant_forge_add_contact_agent_on_evenement_i_cant_see(client, mocked_authentification_user):
    evenement = EvenementFactory(createur=StructureFactory())
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
        "contacts_agents": [Contact.objects.get(agent=mocked_authentification_user.agent)],
    }
    response = client.post(reverse("agent-add"), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.contacts.count() == 0


@pytest.mark.django_db
def test_add_contact_agent_without_value_shows_front_error(live_server, page: Page):
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    validation_message = page.locator("#id_contacts_agents").evaluate("el => el.validationMessage")
    assert validation_message in ["Please select an item in the list.", "Sélectionnez un élément dans la liste."]

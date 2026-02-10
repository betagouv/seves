from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest

from core.constants import MUS_STRUCTURE, SEVES_STRUCTURE
from core.factories import ContactAgentFactory, ContactStructureFactory, StructureFactory
from core.models import Contact
from core.tests.generic_tests.contacts import (
    generic_test_add_contact_agent_to_an_evenement,
    generic_test_add_contact_structure_to_an_evenement,
    generic_test_add_contact_structure_to_an_evenement_with_dedicated_email,
    generic_test_add_multiple_contacts_agents_to_an_evenement,
    generic_test_cant_add_contact_agent_if_he_cant_access_domain,
    generic_test_cant_add_contact_structure_if_any_agent_cant_access_domain,
    generic_test_remove_contact_agent_from_an_evenement,
    generic_test_remove_contact_structure_from_an_evenement,
)
from seves import settings
from seves.settings import SV_GROUP
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


def test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = EvenementFactory()
    generic_test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, evenement, mailoutbox)


def test_remove_contact_agent_from_an_evenement(live_server, page, mailoutbox):
    evenement = EvenementFactory()
    generic_test_remove_contact_agent_from_an_evenement(live_server, page, evenement, mailoutbox)


def test_cant_add_inactive_agent_to_an_evenement(live_server, page, choice_js_cant_pick, goto_contacts):
    contact = ContactAgentFactory()
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)

    choice_js_cant_pick(page, "#add-contact-agent-form .choices", contact.agent.nom, contact.display_with_agent_unit)


def test_cant_add_inactive_structure_to_an_evenement(live_server, page, choice_js_cant_pick, goto_contacts):
    contact = ContactStructureFactory(email="")
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)

    choice_js_cant_pick(page, "#add-contact-structure-form .choices", str(contact), str(contact))


def test_add_multiple_contacts_agents_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = EvenementFactory()
    generic_test_add_multiple_contacts_agents_to_an_evenement(live_server, page, evenement, choice_js_fill, mailoutbox)


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


def test_add_agent_contact_adds_structure_contact(live_server, page, choice_js_fill, goto_contacts):
    """Test que l'ajout d'un contact agent ajoute automatiquement le contact de sa structure"""
    structure_contact = ContactStructureFactory()
    agent_contact = ContactAgentFactory(
        agent__structure=structure_contact.structure, with_active_agent__with_groups=(SV_GROUP,)
    )
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    choice_js_fill(
        page, "#add-contact-agent-form .choices", agent_contact.agent.nom, agent_contact.display_with_agent_unit
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    expect(page.get_by_test_id("contacts-agents").get_by_text(str(agent_contact), exact=True)).to_be_visible()
    expect(
        page.get_by_test_id("contacts-structures").get_by_text(str(agent_contact.agent.structure), exact=True)
    ).to_be_visible()


def test_add_multiple_agent_contacts_adds_structure_contact_once(live_server, page, choice_js_fill, goto_contacts):
    """Test que l'ajout de plusieurs contacts agents de la même structure n'ajoute qu'une seule fois le contact structure"""
    structure_contact = ContactStructureFactory()
    contact_agent_1, contact_agent_2 = ContactAgentFactory.create_batch(
        2, agent__structure=structure_contact.structure, with_active_agent__with_groups=[SV_GROUP]
    )
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    choice_js_fill(
        page,
        "#add-contact-agent-form",
        contact_agent_1.agent.nom,
        contact_agent_1.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    goto_contacts(page)
    page.wait_for_timeout(1000)
    choice_js_fill(
        page,
        "#add-contact-agent-form",
        contact_agent_2.agent.nom,
        contact_agent_2.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    goto_contacts(page)

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
def test_add_contact_agent_without_value_shows_front_error(live_server, page: Page, goto_contacts):
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    validation_message = page.locator("#id_contacts_agents").evaluate("el => el.validationMessage")
    assert validation_message in ["Please select an item in the list.", "Sélectionnez un élément dans la liste."]


def test_cant_see_add_contact_form_if_evenement_is_cloture(live_server, page, goto_contacts):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)

    expect(page.locator("#add-contact-agent-form")).not_to_be_visible()
    expect(page.locator("#add-contact-structure-form")).not_to_be_visible()


def test_cant_forge_add_agent_if_evenement_is_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
        "contacts_agents": [Contact.objects.get(agent=ContactAgentFactory().agent)],
    }
    response = client.post(reverse("agent-add"), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.contacts.count() == 0


def test_cant_forge_add_structure_if_evenement_is_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
        "contacts_structures": [Contact.objects.get(structure=ContactStructureFactory().structure)],
    }
    response = client.post(reverse("structure-add"), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.contacts.count() == 0


@pytest.mark.django_db
def test_add_contact_agent_doesnt_add_structure_if_referent_national(live_server, page, choice_js_fill, goto_contacts):
    contact_agent = ContactAgentFactory(with_active_agent__with_groups=(SV_GROUP,))
    referent_national_group, _ = Group.objects.get_or_create(name=settings.REFERENT_NATIONAL_GROUP)
    contact_agent.agent.user.groups.add(referent_national_group)
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    choice_js_fill(
        page, "#add-contact-agent-form .choices", contact_agent.agent.nom, contact_agent.display_with_agent_unit
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    expect(
        page.get_by_test_id("contacts-structures").get_by_text(str(contact_agent.agent.structure), exact=True)
    ).not_to_be_visible()
    evenement.refresh_from_db()
    assert evenement.contacts.count() == 1
    assert contact_agent.agent.structure not in evenement.contacts.all()


@pytest.fixture
def contacts_structure():
    return ContactStructureFactory.create_batch(2, with_one_active_agent__with_groups=(SV_GROUP,))


@pytest.mark.django_db
def test_add_structure_form_hides_empty_emails(live_server, page):
    evenement = EvenementFactory()
    evenement.contacts.set(ContactStructureFactory.create_batch(5, with_one_active_agent__with_groups=(SV_GROUP,)))

    ContactStructureFactory(structure__libelle="Level 1", with_one_active_agent__with_groups=(SV_GROUP,))
    ContactStructureFactory(structure__libelle="Level 2", with_one_active_agent__with_groups=(SV_GROUP,), email="")
    ContactStructureFactory(structure__libelle="Level 3", with_one_active_agent__with_groups=(SV_GROUP,))

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()

    expect(page.get_by_label("Ajouter une structure").get_by_role("option", name="Level 1", exact=True)).to_be_visible()
    expect(
        page.get_by_label("Ajouter une structure").get_by_role("option", name="Level 2", exact=True)
    ).not_to_be_visible()
    expect(page.get_by_label("Ajouter une structure").get_by_role("option", name="Level 3", exact=True)).to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_hides_structure_without_active_user(live_server, page):
    visible_structure = ContactStructureFactory(with_one_active_agent__with_groups=(SV_GROUP,))
    unvisible_structure = ContactStructureFactory()

    page.goto(f"{live_server.url}{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()

    expect(
        page.get_by_label("Ajouter une structure").get_by_role(
            "option", name=str(visible_structure.structure), exact=True
        )
    ).to_be_visible()
    expect(
        page.get_by_label("Ajouter une structure").get_by_role(
            "option", name=str(unvisible_structure.structure), exact=True
        )
    ).not_to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_service_account_is_hidden(live_server, page):
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()
    expect(page.get_by_text("service_account")).not_to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_seves_is_hidden(live_server, page):
    contact = ContactStructureFactory(structure__niveau1=SEVES_STRUCTURE, structure__libelle=SEVES_STRUCTURE)
    ContactAgentFactory(with_active_agent__with_groups=[settings.SV_GROUP], agent__structure=contact.structure)
    page.goto(f"{live_server.url}{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()

    expect(page.get_by_text(SEVES_STRUCTURE)).not_to_be_visible()


@pytest.mark.django_db
def test_can_add_structure_with_no_active_contacts_when_forced_is_true(live_server, page):
    contact = ContactStructureFactory(structure__niveau1="DDPP59", structure__libelle="DDPP59")
    page.goto(f"{live_server.url}{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()
    expect(page.get_by_text("DDPP59")).not_to_be_visible()

    structure = contact.structure
    structure.force_can_be_contacted = True
    structure.save()

    page.goto(f"{live_server.url}{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()
    expect(page.locator(".choices__item--selectable").get_by_text("DDPP59", exact=True)).to_be_visible()


@pytest.mark.django_db
def test_structure_niveau2_without_emails_are_not_visible(live_server, page):
    ContactStructureFactory(
        structure__niveau1="Level 1", structure__libelle="Foo", with_one_active_agent__with_groups=(SV_GROUP,)
    )
    ContactStructureFactory(
        structure__niveau1="Level 1", structure__libelle="Bar", with_one_active_agent__with_groups=(SV_GROUP,), email=""
    )
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.query_selector("#add-contact-structure-form .choices").click()

    expect(page.get_by_label("Ajouter une structure").get_by_role("option", name="Foo")).to_be_visible()
    expect(page.get_by_label("Ajouter une structure").get_by_role("option", name="Bar")).not_to_be_visible()


def test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = EvenementFactory()
    generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, evenement, mailoutbox)


def test_remove_contact_structure_from_an_evenement(live_server, page, mailoutbox):
    evenement = EvenementFactory()
    generic_test_remove_contact_structure_from_an_evenement(live_server, page, evenement, mailoutbox)


@pytest.mark.django_db
def test_add_multiple_structures_to_an_evenement(live_server, page, choice_js_fill):
    contact_structure_1, contact_structure_2 = ContactStructureFactory.create_batch(
        2, with_one_active_agent__with_groups=(SV_GROUP,)
    )
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    choice_js_fill(page, "#add-contact-structure-form .choices", str(contact_structure_1), str(contact_structure_1))
    choice_js_fill(page, "#add-contact-structure-form .choices", str(contact_structure_2), str(contact_structure_2))
    page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()

    expect(page.get_by_text("Les 2 structures ont été ajoutées avec succès.")).to_be_visible()
    page.get_by_role("tab", name="Contacts").click()
    assert page.get_by_test_id("contacts-structures").count() == 2
    expect(page.get_by_test_id("contacts-structures").get_by_text(str(contact_structure_1), exact=True)).to_be_visible()
    expect(page.get_by_test_id("contacts-structures").get_by_text(str(contact_structure_2), exact=True)).to_be_visible()


@pytest.mark.django_db
def test_cant_add_contact_structure_if_evenement_brouillon(client):
    contact = ContactStructureFactory(with_one_active_agent__with_groups=(SV_GROUP,))
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    response = client.post(
        reverse("structure-add"),
        data={
            "contacts_structures": [contact.id],
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "content_id": evenement.id,
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


@pytest.mark.django_db
@pytest.mark.browser_context_args(timezone_id="Europe/Berlin", locale="de-DE")
def test_add_contact_structure_without_value_shows_front_error(live_server, page: Page):
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()

    validation_message = page.locator("#id_contacts_structures").evaluate("el => el.validationMessage")
    assert validation_message in ["Please select an item in the list.", "Sélectionnez un élément dans la liste."]


def test_add_contact_structure_to_an_evenement_with_dedicated_email(live_server, page, choice_js_fill, mailoutbox):
    evenement = EvenementFactory()
    generic_test_add_contact_structure_to_an_evenement_with_dedicated_email(
        live_server, page, choice_js_fill, evenement, mailoutbox, domain="sv"
    )


def test_cant_add_contact_agent_if_he_cant_access_domain(live_server, page, choice_js_cant_pick):
    evenement = EvenementFactory()
    generic_test_cant_add_contact_agent_if_he_cant_access_domain(
        live_server,
        page,
        choice_js_cant_pick,
        evenement,
    )


def test_cant_add_contact_structure_if_any_agent_cant_access_domain(live_server, page, choice_js_cant_pick):
    evenement = EvenementFactory()
    generic_test_cant_add_contact_structure_if_any_agent_cant_access_domain(
        live_server,
        page,
        choice_js_cant_pick,
        evenement,
    )

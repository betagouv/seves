import pytest
from playwright.sync_api import expect

from core.factories import ContactAgentFactory, StructureFactory, ContactStructureFactory
from core.models import Contact
from seves import settings
from sv.factories import EvenementFactory


@pytest.mark.django_db
def test_contacts_agents_order_in_list(live_server, page):
    evenement = EvenementFactory()
    structure_bsv = StructureFactory(niveau1="AC/DAC/DGAL", niveau2="BSV", libelle="BSV")
    structure_ddpp17 = StructureFactory(niveau1="DDI/DDPP", niveau2="DDPP17", libelle="DDPP17")
    structure_mus = StructureFactory(niveau1="AC/DAC/DGAL", niveau2="MUS", libelle="MUS")
    contacts_in_expected_order = [
        ContactAgentFactory(
            agent__structure=structure_bsv, agent__nom="Dubois", agent__prenom="Martin", with_active_agent=True
        ),
        ContactAgentFactory(
            agent__structure=structure_bsv, agent__nom="Martin", agent__prenom="Sophie", with_active_agent=True
        ),
        ContactAgentFactory(
            agent__structure=structure_ddpp17, agent__nom="Bernard", agent__prenom="Camille", with_active_agent=True
        ),
        ContactAgentFactory(
            agent__structure=structure_ddpp17, agent__nom="Leroy", agent__prenom="Julie", with_active_agent=True
        ),
        ContactAgentFactory(
            agent__structure=structure_ddpp17, agent__nom="Moreau", agent__prenom="Lucas", with_active_agent=True
        ),
        ContactAgentFactory(
            agent__structure=structure_mus, agent__nom="Petit", agent__prenom="Thomas", with_active_agent=True
        ),
    ]
    evenement.contacts.set(contacts_in_expected_order)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    for i, contact in enumerate(contacts_in_expected_order):
        agent_full_name = f"{contact.agent.nom} {contact.agent.prenom}"
        structure_name = contact.agent.structure.libelle
        contact_element = page.get_by_test_id("contacts-agents").nth(i)
        expect(contact_element).to_contain_text(agent_full_name)
        expect(contact_element).to_contain_text(structure_name)


@pytest.mark.django_db
def test_contacts_structures_order_in_list(
    live_server,
    page,
):
    evenement = EvenementFactory()
    contact_bsv = ContactStructureFactory(
        structure__niveau1="AC/DAC/DGAL", structure__niveau2="BSV", structure__libelle="BSV"
    )
    contact_ddpp17 = ContactStructureFactory(
        structure__niveau1="DDI/DDPP", structure__niveau2="DDPP17", structure__libelle="DDPP17"
    )
    contact_mus = ContactStructureFactory(
        structure__niveau1="AC/DAC/DGAL", structure__niveau2="MUS", structure__libelle="MUS"
    )
    contacts_in_expected_order = [contact_bsv, contact_ddpp17, contact_mus]
    evenement.contacts.set(contacts_in_expected_order)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    for i, contact in enumerate(contacts_in_expected_order):
        expect(page.get_by_test_id("contacts-structures").nth(i)).to_contain_text(str(contact))


def test_when_structure_is_in_fin_suivi_all_agents_should_be_in_fin_suivi(
    live_server, page, mocked_authentification_user
):
    evenement = EvenementFactory()
    contact_structure = Contact.objects.get(email="structure_test@test.fr")
    contact_agent_1 = Contact.objects.get(email="text@example.com")
    contact_agent_2 = ContactAgentFactory(agent__structure=contact_structure.structure)
    evenement.contacts.set([contact_agent_1, contact_agent_2, contact_structure])

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Signaler la fin de suivi").click()
    page.get_by_test_id("contacts").click()

    contacts_agents = page.get_by_test_id("contacts-agents")
    for contact in contacts_agents.all():
        expect(contact).to_contain_text("Fin de suivi")


def test_click_on_contact_agent_name_opens_message(live_server, page, choice_js_get_values):
    evenement = EvenementFactory()
    contact_agent = ContactAgentFactory(with_active_agent__with_groups=(settings.SV_GROUP,))
    evenement.contacts.set([contact_agent])

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_test_id("contacts-agents").locator("a.email").click()
    page.wait_for_url("**core/message-add**")

    expect(page.locator("h1")).to_have_text("Nouveau message")
    assert choice_js_get_values(page, "label[for='id_recipients']", delete_remove_link=True) == [
        contact_agent.agent.agent_with_structure
    ]


def test_click_on_contact_structure_name_opens_message(live_server, page, choice_js_get_values):
    evenement = EvenementFactory()
    contact_agent = ContactStructureFactory(with_one_active_agent__with_groups=(settings.SV_GROUP,))
    evenement.contacts.set([contact_agent])

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_test_id("contacts-structures").locator("a.email").click()
    page.wait_for_url("**core/message-add**")

    expect(page.locator("h1")).to_have_text("Nouveau message")
    assert choice_js_get_values(page, "label[for='id_recipients']", delete_remove_link=True) == [
        str(contact_agent.structure)
    ]

from playwright.sync_api import expect

from core.factories import ContactStructureFactory, ContactAgentFactory
from core.pages import WithContactsPage


def generic_test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, object):
    contact_structure = ContactStructureFactory()
    contact = ContactAgentFactory(with_active_agent=True, agent__structure=contact_structure.structure)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.add_agent(choice_js_fill, contact)

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("L'agent a été ajouté avec succès.")).to_be_visible()
    expect(page.get_by_test_id("contacts-agents")).to_be_visible()
    assert page.get_by_test_id("contacts-agents").count() == 1
    assert object.__class__.objects.filter(pk=object.pk, contacts=contact).exists()


def generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, object):
    contact_structure = ContactStructureFactory(with_one_active_agent=True)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.add_structure(choice_js_fill, contact_structure)

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("La structure a été ajoutée avec succès.")).to_be_visible()
    expect(page.get_by_test_id("contacts-structures")).to_be_visible()
    assert page.get_by_test_id("contacts-structures").count() == 1
    assert object.__class__.objects.filter(pk=object.pk, contacts=contact_structure).exists()

from model_bakery import baker
from playwright.sync_api import expect

from core.models import Contact, Agent


def test_can_remove_myself_from_a_fiche(live_server, page, fiche_variable, mocked_authentification_user):
    fiche = fiche_variable()
    contact = mocked_authentification_user.agent.contact_set.get()
    fiche.contacts.set([contact])
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    page.locator(f'a[aria-controls="fr-modal-contact-{contact.id}"]').click()
    expect(page.get_by_text(str(mocked_authentification_user.agent), exact=True)).to_be_visible()
    expect(page.locator(f"#fr-modal-contact-{contact.id}")).to_be_visible()
    page.get_by_test_id(f"contact-delete-{contact.id}").click()

    assert page.url == f"{live_server.url}{fiche.get_absolute_url()}#tabpanel-contacts-panel"
    assert fiche.contacts.count() == 0
    expect(page.get_by_text(str(mocked_authentification_user.agent), exact=True)).not_to_be_visible()


def test_can_remove_another_contact_from_a_fiche(live_server, page, fiche_variable):
    fiche = fiche_variable()
    agent = baker.make(Agent)
    contact = baker.make(Contact, agent=agent)
    fiche.contacts.set([contact])
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    page.locator(f'a[aria-controls="fr-modal-contact-{contact.id}"]').click()
    expect(page.get_by_text(str(agent), exact=True)).to_be_visible()
    expect(page.locator(f"#fr-modal-contact-{contact.id}")).to_be_visible()
    page.get_by_test_id(f"contact-delete-{contact.id}").click()

    assert page.url == f"{live_server.url}{fiche.get_absolute_url()}#tabpanel-contacts-panel"
    assert fiche.contacts.count() == 0
    expect(page.get_by_text(str(agent), exact=True)).not_to_be_visible()

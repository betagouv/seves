from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from model_bakery import baker
from playwright.sync_api import expect

from core.factories import ContactAgentFactory
from core.models import Contact, Agent, Structure
from sv.factories import EvenementFactory


def test_can_remove_myself_from_an_evenement(live_server, page, mocked_authentification_user):
    evenement = EvenementFactory()
    contact = mocked_authentification_user.agent.contact_set.get()
    evenement.contacts.set([contact])
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    page.locator(f'a[aria-controls="fr-modal-contact-{contact.id}"]').click()
    expect(
        page.get_by_test_id("contacts-agents").get_by_text(str(mocked_authentification_user.agent), exact=True)
    ).to_be_visible()
    expect(page.locator(f"#fr-modal-contact-{contact.id}")).to_be_visible()
    page.get_by_test_id(f"contact-delete-{contact.id}").click()

    assert page.url == f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-contacts-panel"
    assert evenement.contacts.count() == 0
    expect(
        page.get_by_test_id("contacts-agents").get_by_text(str(mocked_authentification_user.agent), exact=True)
    ).not_to_be_visible()


def test_can_remove_another_contact_from_a_fiche(live_server, page):
    evenement = EvenementFactory()
    agent = baker.make(Agent)
    contact = baker.make(Contact, agent=agent)
    evenement.contacts.set([contact])
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    page.locator(f'a[aria-controls="fr-modal-contact-{contact.id}"]').click()
    expect(page.get_by_text(str(agent), exact=True)).to_be_visible()
    expect(page.locator(f"#fr-modal-contact-{contact.id}")).to_be_visible()
    page.get_by_test_id(f"contact-delete-{contact.id}").click()

    assert page.url == f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-contacts-panel"
    assert evenement.contacts.count() == 0
    expect(page.get_by_text(str(agent), exact=True)).not_to_be_visible()


def test_cant_forge_contact_deletion_of_evenement_i_cant_see(client):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    contact = ContactAgentFactory()
    evenement.contacts.set([contact])
    assert evenement.contacts.count() == 1
    content_type = ContentType.objects.get_for_model(evenement).pk

    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "fiche_pk": evenement.pk,
        "content_type_pk": content_type,
        "pk": contact.pk,
        "next": evenement.get_absolute_url(),
    }
    response = client.post(reverse("contact-delete"), data=payload)

    assert response.status_code == 403
    assert evenement.contacts.count() == 1

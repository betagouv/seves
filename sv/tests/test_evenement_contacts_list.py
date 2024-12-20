import pytest
from model_bakery import baker
from playwright.sync_api import expect
from core.models import Contact, Structure, Agent
from sv.factories import EvenementFactory


@pytest.mark.django_db
def test_contacts_agents_order_in_list(live_server, page):
    evenement = EvenementFactory()
    structure_mus = Structure.objects.create(niveau1="AC/DAC/DGAL", niveau2="MUS", libelle="MUS")
    structure_ddpp17 = Structure.objects.create(niveau1="DDI/DDPP", niveau2="DDPP17", libelle="DDPP17")
    agent1 = baker.make(Agent, structure=structure_mus)
    agent2 = baker.make(Agent, structure=structure_ddpp17)
    contact1 = Contact.objects.create(agent=agent1)
    contact2 = Contact.objects.create(agent=agent2)
    evenement.contacts.set([contact1, contact2])

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    expect(page.locator(".fr-card__content").first).to_contain_text(f"{contact2.agent.nom} {contact2.agent.prenom}")
    expect(page.locator(".fr-card__content").first).to_contain_text(contact2.agent.structure.libelle)
    expect(page.locator(".fr-card__content").last).to_contain_text(f"{contact1.agent.nom} {contact1.agent.prenom}")
    expect(page.locator(".fr-card__content").last).to_contain_text(contact1.agent.structure.libelle)


@pytest.mark.django_db
def test_contacts_structures_order_in_list(
    live_server,
    page,
):
    evenement = EvenementFactory()
    structure_mus = Structure.objects.create(niveau1="AC/DAC/DGAL", niveau2="MUS", libelle="MUS")
    structure_ddpp17 = Structure.objects.create(niveau1="DDI/DDPP", niveau2="DDPP17", libelle="DDPP17")
    contact1 = Contact.objects.create(structure=structure_mus)
    contact2 = Contact.objects.create(structure=structure_ddpp17)
    evenement.contacts.set([contact1, contact2])

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    expect(page.locator(".fr-card__content").first).to_contain_text(contact2.structure.libelle)
    expect(page.locator(".fr-card__content").last).to_contain_text(contact1.structure.libelle)


def test_when_structure_is_in_fin_suivi_all_agents_should_be_in_fin_suivi(
    live_server, page, mocked_authentification_user
):
    evenement = EvenementFactory()
    contact_structure = Contact.objects.get(email="structure_test@test.fr")
    contact_agent_1 = Contact.objects.get(email="text@example.com")
    contact_agent_2 = Contact.objects.create(agent=baker.make(Agent, structure=contact_structure.structure))
    evenement.contacts.set([contact_agent_1, contact_agent_2, contact_structure])

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Signaler la fin de suivi").click()
    page.get_by_label("Message").fill("aaa")
    page.get_by_test_id("fildesuivi-add-submit").click()
    page.get_by_test_id("contacts").click()

    contacts_agents = page.get_by_test_id("contacts-agents")
    for contact in contacts_agents.all():
        expect(contact).to_contain_text("Fin de suivi")

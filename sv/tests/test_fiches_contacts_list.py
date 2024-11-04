import pytest
from model_bakery import baker
from playwright.sync_api import expect
from core.models import Contact, Structure, Agent


@pytest.mark.django_db
def test_contacts_agents_order_in_list(live_server, page, fiche_variable):
    "Test l'ordre d'affichage des contacts (agents) dans la liste"
    fiche = fiche_variable()
    structure_mus = Structure.objects.create(niveau1="AC/DAC/DGAL", niveau2="MUS", libelle="MUS")
    structure_ddpp17 = Structure.objects.create(niveau1="DDI/DDPP", niveau2="DDPP17", libelle="DDPP17")
    agent1 = baker.make(Agent, structure=structure_mus)
    agent2 = baker.make(Agent, structure=structure_ddpp17)
    contact1 = Contact.objects.create(agent=agent1)
    contact2 = Contact.objects.create(agent=agent2)
    fiche.contacts.set([contact1, contact2])

    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    expect(page.locator(".fr-card__content").first).to_contain_text(f"{contact2.agent.nom} {contact2.agent.prenom}")
    expect(page.locator(".fr-card__content").first).to_contain_text(contact2.agent.structure.libelle)
    expect(page.locator(".fr-card__content").last).to_contain_text(f"{contact1.agent.nom} {contact1.agent.prenom}")
    expect(page.locator(".fr-card__content").last).to_contain_text(contact1.agent.structure.libelle)


@pytest.mark.django_db
def test_contacts_structures_order_in_list(live_server, page, fiche_variable):
    "Test l'ordre d'affichage des contacts (structures) dans la liste"
    fiche = fiche_variable()
    structure_mus = Structure.objects.create(niveau1="AC/DAC/DGAL", niveau2="MUS", libelle="MUS")
    structure_ddpp17 = Structure.objects.create(niveau1="DDI/DDPP", niveau2="DDPP17", libelle="DDPP17")
    contact1 = Contact.objects.create(structure=structure_mus)
    contact2 = Contact.objects.create(structure=structure_ddpp17)
    fiche.contacts.set([contact1, contact2])

    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()

    expect(page.locator(".fr-card__content").first).to_contain_text(contact2.structure.libelle)
    expect(page.locator(".fr-card__content").last).to_contain_text(contact1.structure.libelle)

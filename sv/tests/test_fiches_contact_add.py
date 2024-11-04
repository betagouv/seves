import pytest
from playwright.sync_api import expect
from model_bakery import baker
from django.urls import reverse

from core.models import Contact, Structure, Agent


@pytest.fixture
def contact(db):
    structure = baker.make(Structure, _fill_optional=True)
    return baker.make(Contact, agent=baker.make(Agent, structure=structure))


@pytest.fixture
def contacts(db):
    # creation de deux contacts de type Agent
    agent1, agent2 = baker.make(Agent, _quantity=2)
    baker.make(Contact, agent=agent1)
    baker.make(Contact, agent=agent2)
    # création de la structure MUS et de deux contacts de type Agent associés
    structure_mus = baker.make(Structure, libelle="MUS")
    agentMUS1, agentMUS2 = baker.make(Agent, _quantity=2, structure=structure_mus)
    contactMUS1 = baker.make(Contact, agent=agentMUS1)
    contactMUS2 = baker.make(Contact, agent=agentMUS2)
    return [contactMUS1, contactMUS2]


def test_add_contact_form(live_server, page, fiche_variable, mocked_authentification_user):
    """Test l'affichage du formulaire d'ajout de contact"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()

    expect(page.get_by_role("link", name="Retour à la fiche")).to_be_visible()
    expect(page.get_by_role("heading", name="Ajouter un agent")).to_be_visible()
    expect(page.get_by_text("Structure", exact=True)).to_be_visible()
    expect(page.get_by_text(mocked_authentification_user.agent.structure.libelle).nth(1)).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


def test_add_contact_form_back_to_fiche(live_server, page, fiche_variable):
    """Test le lien de retour vers la fiche"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")


@pytest.mark.django_db
def test_structure_list(client):
    """Test que la liste des structures soit bien dans le contexte du formulaire d'ajout de contact"""
    Contact.objects.all().delete()
    Agent.objects.all().delete()
    Structure.objects.all().delete()
    baker.make(Structure, _quantity=3)
    url = reverse("contact-add-form")
    response = client.get(url)
    form = response.context["form"]
    form_structures = form.fields["structure"].queryset
    assert form_structures.count() == 3
    assert all(structure in form_structures for structure in Structure.objects.all())


def test_add_contact_form_select_structure(live_server, page, fiche_variable, contacts, choice_js_fill):
    """Test l'affichage des contacts dans le formulaire de sélection suite à la selection d'une structure"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    contact1 = contacts[0]
    contact2 = contacts[1]
    expect(page.get_by_text(f"{contact1.agent.nom}")).to_be_visible()
    expect(page.get_by_text(f"{contact1.agent.nom}")).to_contain_text(f"{contact1.agent.nom} {contact1.agent.prenom}")
    expect(page.get_by_text(f"{contact2.agent.nom}")).to_be_visible()
    expect(page.get_by_text(f"{contact2.agent.nom}")).to_contain_text(f"{contact2.agent.nom} {contact2.agent.prenom}")


def test_add_contact_to_a_fiche(live_server, page, fiche_variable, contacts, choice_js_fill):
    """Test l'ajout d'un contact à une fiche de détection"""
    fiche = fiche_variable()
    contact1 = contacts[0]
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(f"{contact1.agent.nom} {contact1.agent.prenom}").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("tab", name="Contacts").click()

    expect(page.get_by_text("Le contact a été ajouté avec succès.")).to_be_visible()
    expect(page.locator(".fr-card__content")).to_be_visible()


def test_add_multiple_contacts_to_a_fiche(live_server, page, fiche_variable, contacts, choice_js_fill):
    """Test l'ajout de plusieurs contacts à une fiche de détection"""
    fiche = fiche_variable()
    contact1 = contacts[0]
    contact2 = contacts[1]
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(f"{contact1.agent.nom} {contact1.agent.prenom}").click()
    page.get_by_text(f"{contact2.agent.nom} {contact2.agent.prenom}").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.get_by_text("Les 2 contacts ont été ajoutés avec succès.")).to_be_visible()
    page.get_by_role("tab", name="Contacts").click()
    expect(page.locator(".fr-card__content").first).to_be_visible()
    expect(page.locator("div:nth-child(2) > .fr-card > .fr-card__body > .fr-card__content")).to_be_visible()


def test_no_contact_selected(live_server, page, fiche_variable, contact, choice_js_fill):
    """Test l'affichage d'un message d'erreur si aucun contact n'est sélectionné"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.get_by_text("Veuillez sélectionner au")).to_be_visible()
    expect(page.locator("#form-selection")).to_contain_text("Veuillez sélectionner au moins un contact")


def test_add_contact_form_back_to_fiche_after_select_structure(
    live_server, page, fiche_variable, contact, choice_js_fill
):
    """Test le lien de retour vers la fiche après la selection d'une structure et l'affichage des contacts associés"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")


def test_add_contact_form_back_to_fiche_after_error_message(live_server, page, fiche_variable, contact, choice_js_fill):
    """Test le lien de retour vers la fiche après l'affichage du message d'erreur si aucun contact n'est sélectionné"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")

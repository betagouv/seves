import pytest
import json
from playwright.sync_api import expect
from model_bakery import baker
from sv.models import Contact


@pytest.fixture
def contact():
    return baker.make(Contact)


@pytest.fixture
def contacts():
    baker.make(Contact, _quantity=2)
    return baker.make(Contact, structure="MUS", _quantity=2)


def test_add_contact_form(live_server, page, fiche_detection):
    """Test l'affichage du formulaire d'ajout de contact"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()

    expect(page.get_by_role("link", name="Retour à la fiche")).to_be_visible()
    expect(page.get_by_role("heading", name="Ajouter un agent")).to_be_visible()
    expect(page.get_by_text("Structure")).to_be_visible()
    expect(page.get_by_text("Choisir dans la listeChoisir")).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


def test_add_contact_form_back_to_fiche(live_server, page, fiche_detection):
    """Test le lien de retour vers la fiche"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche_detection.get_absolute_url()}")


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_structure_list(live_server, page, fiche_detection):
    """test que le champ structure contient la liste des structures et la valeur par défaut "Choisir dans la liste" """
    baker.make(Contact, structure="MUS", _quantity=3)
    contacts = baker.make(Contact, _quantity=2)

    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()

    structures_json = page.locator("#structures-json").inner_text()
    structures = json.loads(structures_json)
    assert len(structures) == 4

    structures_names = [structure_name for _, structure_name in structures]
    expected_structures_names = ["Choisir dans la liste", "MUS", contacts[0].structure, contacts[1].structure]
    assert set(structures_names) == set(expected_structures_names)


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_add_contact_form_select_structure(live_server, page, fiche_detection, contacts):
    """Test l'affichage des contacts dans le formulaire de sélection suite à la selection d'une structure"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_text("Choisir dans la liste").nth(1).click()
    page.get_by_role("option", name="MUS Press to select").click()
    page.get_by_role("button", name="Rechercher").click()
    contact1 = contacts[0]
    contact2 = contacts[1]
    expect(page.get_by_text(f"MUS - {contact1.nom}")).to_be_visible()
    expect(page.get_by_text(f"MUS - {contact1.nom}")).to_contain_text(f"{contact1.structure} - {contact1.nom}")
    expect(page.get_by_text(f"MUS - {contact2.nom}")).to_be_visible()
    expect(page.get_by_text(f"MUS - {contact2.nom}")).to_contain_text(f"{contact2.structure} - {contact2.nom}")


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_add_contact_to_a_fiche(live_server, page, fiche_detection, contacts):
    """Test l'ajout d'un contact à une fiche de détection"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_text("Choisir dans la liste").nth(1).click()
    page.get_by_role("option", name="MUS Press to select").click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text("MUS -").first.click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("tab", name="Contacts").click()

    expect(page.get_by_text("Le contact a été ajouté avec succès.")).to_be_visible()
    expect(page.locator(".fr-card__content")).to_be_visible()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_add_multiple_contacts_to_a_fiche(live_server, page, fiche_detection, contacts):
    """Test l'ajout de plusieurs contacts à une fiche de détection"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_text("Choisir dans la liste").nth(1).click()
    page.get_by_role("option", name="MUS Press to select").click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text("MUS -").first.click()
    page.get_by_text("MUS -").nth(1).click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.get_by_text("Les 2 contacts ont été ajoutés avec succès.")).to_be_visible()
    page.get_by_role("tab", name="Contacts").click()
    expect(page.locator(".fr-card__content").first).to_be_visible()
    expect(page.locator("div:nth-child(2) > .fr-card > .fr-card__body > .fr-card__content")).to_be_visible()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_no_contact_selected(live_server, page, fiche_detection, contact):
    """Test l'affichage d'un message d'erreur si aucun contact n'est sélectionné"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_text("Choisir dans la liste").nth(1).click()
    page.get_by_role("option", name=f"{contact.structure} Press to select").click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.get_by_text("Veuillez sélectionner au")).to_be_visible()
    expect(page.locator("#form-selection")).to_contain_text("Veuillez sélectionner au moins un contact")


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_add_contact_form_back_to_fiche_after_select_structure(live_server, page, fiche_detection, contact):
    """Test le lien de retour vers la fiche après la selection d'une structure et l'affichage des contacts associés"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_text("Choisir dans la liste").nth(1).click()
    page.get_by_role("option", name=f"{contact.structure}").click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche_detection.get_absolute_url()}")


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_add_contact_form_back_to_fiche_after_error_message(live_server, page, fiche_detection, contact):
    """Test le lien de retour vers la fiche après l'affichage du message d'erreur si aucun contact n'est sélectionné"""
    page.goto(f"{live_server.url}/{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_text("Choisir dans la liste").nth(1).click()
    page.get_by_role("option", name=f"{contact.structure} Press to select").click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche_detection.get_absolute_url()}")

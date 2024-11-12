import pytest
from playwright.sync_api import expect
from model_bakery import baker
from core.models import Structure, Contact


@pytest.fixture
def contacts_structure():
    structure1, structure2 = baker.make(Structure, _quantity=2, _fill_optional=True)
    contact1 = baker.make(Contact, structure=structure1)
    contact2 = baker.make(Contact, structure=structure2)
    return [contact1, contact2]


@pytest.mark.django_db
def test_add_structure_form(live_server, page, fiche_variable, contacts_structure):
    """Test l'affichage du formulaire d'ajout de structure"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()

    expect(page.get_by_role("link", name="Retour à la fiche")).to_be_visible()
    expect(page.get_by_role("heading", name="Ajouter une structure")).to_be_visible()
    expect(page.get_by_text("En :")).to_be_visible()
    expect(page.get_by_text(contacts_structure[0].structure.niveau1)).to_be_visible()
    expect(page.get_by_text(contacts_structure[1].structure.niveau1)).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_service_account_is_hidden(live_server, page, fiche_variable):
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    expect(page.get_by_text("service_account")).not_to_be_visible()


def test_add_structure_form_back_to_fiche(live_server, page, fiche_variable):
    """Test le lien de retour vers la fiche"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")


@pytest.mark.django_db
def test_structure_niveau2_are_visible_aftert_select_structure_niveau1(
    live_server, page, fiche_variable, contacts_structure
):
    """Test l'affichage des structures de niveau 2 suite à la selection d'une structure de niveau 1"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()

    for contact in contacts_structure:
        page.get_by_text(contact.structure.niveau1).click()
        page.get_by_role("button", name="Rechercher").click()
        expect(page.get_by_text(contact.structure.libelle)).to_be_visible()


@pytest.mark.django_db
def test_add_structure_to_a_fiche(live_server, page, fiche_variable, contacts_structure):
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contacts_structure[0].structure.niveau1).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(contacts_structure[0].structure.libelle).click()
    page.get_by_role("button", name="Ajouter les structures sélectionnées").click()
    expect(page.get_by_text("La structure a été ajoutée avec succès.")).to_be_visible()
    expect(page.locator("p").filter(has_text=contacts_structure[0].structure.libelle)).to_be_visible()


@pytest.mark.django_db
def test_add_multiple_structures_to_a_fiche(live_server, page, fiche_variable):
    fiche = fiche_variable()
    structure1, structure2 = baker.make(Structure, niveau1="AC", _quantity=2, _fill_optional=True)
    contact1 = baker.make(Contact, structure=structure1)
    contact2 = baker.make(Contact, structure=structure2)

    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contact1.structure.niveau1, exact=True).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(contact1.structure.libelle).click()
    page.get_by_text(contact2.structure.libelle).click()
    page.get_by_role("button", name="Ajouter les structures sélectionnées").click()

    expect(page.get_by_text("Les 2 structures ont été ajoutées avec succès.")).to_be_visible()
    expect(page.locator(".bloc-commun__panel--contacts")).to_contain_text(contact1.structure.libelle)
    expect(page.locator(".bloc-commun__panel--contacts")).to_contain_text(contact2.structure.libelle)


@pytest.mark.django_db
def test_no_structure_selected(live_server, page, fiche_variable, contacts_structure):
    """Test l'affichage d'un message d'erreur si aucune structure n'est sélectionné lors de l'envoi du formulaire"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contacts_structure[0].structure.niveau1).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les structures sélectionnées").click()
    expect(page.get_by_text("Veuillez sélectionner au moins une structure")).to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_back_to_fiche_after_select_structure_niveau1(
    live_server, page, fiche_variable, contacts_structure
):
    """Test le retour à la fiche après avoir sélectionné une structure de niveau 1"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contacts_structure[0].structure.niveau1).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")

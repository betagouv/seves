from playwright.sync_api import Page

from core.factories import DepartementFactory
from sa.models import EvenementAnimal, Veterinaire
from sa.tests.factories import (
    EspeceFactory,
    EvenementAnimalFactory,
    MaladieFactory,
    VeterinaireFactory,
)
from sa.tests.pages import EvenementAnimalDetailsPage, EvenementAnimalFormPage

FIELDS_TO_EXCLUDE_VETERINAIRE = ["_state", "id", "evenement_id"]


def test_can_add_veterinaire(live_server, page: Page, assert_models_are_equal):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    veterinaire = VeterinaireFactory.build(departement=DepartementFactory(), commune="Lille", code_insee="59350")

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.add_veterinaire(veterinaire)

    assert creation_page.nb_veterinaire == 1

    creation_page.submit_as_draft()

    saved_veterinaire = EvenementAnimal.objects.get().veterinaires.get()
    assert_models_are_equal(veterinaire, saved_veterinaire, to_exclude=FIELDS_TO_EXCLUDE_VETERINAIRE)
    assert list(saved_veterinaire.especes.all()) == [espece]


def test_deleting_or_cancelling_veterinaire_does_not_save_it(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    veterinaire = VeterinaireFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    # Open modal, fill and delete
    creation_page.add_veterinaire(veterinaire)
    creation_page.delete_veterinaire(0)

    # Open modal and cancel
    creation_page.open_veterinaire_modal()
    creation_page.current_modal.get_by_role("button", name="Annuler").click()
    creation_page.current_modal.wait_for(state="hidden", timeout=2_000)

    creation_page.submit_as_draft()
    assert EvenementAnimal.objects.get().veterinaires.count() == 0


def test_add_button_is_disabled_after_five_veterinaires(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    for _ in range(5):
        creation_page.add_veterinaire(VeterinaireFactory.build())

    assert creation_page.nb_veterinaire == 5
    assert creation_page.add_veterinaire_button.is_disabled()

    creation_page.submit_as_draft()
    assert EvenementAnimal.objects.get().veterinaires.count() == 5


def test_nom_structure_is_required(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    modal = creation_page.open_veterinaire_modal()
    modal.locator('[id$="-nom"]').fill("Dupont")
    modal.get_by_role("button", name="Enregistrer").click()

    assert creation_page.nb_veterinaire == 0
    assert modal.locator('[id$="-nom_structure"]').evaluate("e => e.checkValidity()") is False
    modal.wait_for(state="visible")


def test_single_espece_is_checked_by_default(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    modal = creation_page.open_veterinaire_modal()
    espece_checkboxes = modal.locator('input[type="checkbox"][name$="-especes"]')
    assert espece_checkboxes.count() == 1
    assert espece_checkboxes.first.is_checked()


def test_veterinaire_is_displayed_readonly_on_details_page(live_server, page: Page):
    espece = EspeceFactory()
    evenement = EvenementAnimalFactory(espece=espece)
    veterinaire = VeterinaireFactory(evenement=evenement, especes=[espece])

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.nb_veterinaire == 1
    card = details_page.get_veterinaire_card(0)
    card.get_by_text(veterinaire.nom_structure, exact=True).wait_for(state="visible")
    assert veterinaire.get_type_veterinaire_display().upper() in card.inner_text()
    assert espece.name.upper() in card.inner_text().upper()
    assert card.locator(".modify-button").count() == 0
    assert card.get_by_role("button", name="Supprimer").count() == 0

    modal = details_page.open_veterinaire_detail(0)
    assert veterinaire.nom_structure in modal.inner_text()


def test_deleting_evenement_deletes_its_veterinaires(live_server, page: Page, db):
    veterinaire = VeterinaireFactory()
    evenement_id = veterinaire.evenement_id

    EvenementAnimal.objects.get(pk=evenement_id).delete()

    assert Veterinaire.objects.filter(evenement_id=evenement_id).count() == 0

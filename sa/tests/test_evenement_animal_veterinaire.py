from django.urls import reverse
from playwright.sync_api import Page, expect

from core.factories import DepartementFactory
from core.mixins import WithEtatMixin
from sa.models import EvenementAnimal, Veterinaire
from sa.tests.factories import (
    EspeceConcerneeFactory,
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
    assert list(saved_veterinaire.especes_concernees.all()) == [EvenementAnimal.objects.get().especes_exposees.get()]


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


def test_single_espece_is_checked_and_cannot_be_unchecked(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_espece_concernee(0, identifiant="123456789")

    modal = creation_page.open_veterinaire_modal()
    espece_checkboxes = creation_page.get_veterinaire_especes_checkboxes(modal)
    expect(espece_checkboxes).to_have_count(1)
    expect(espece_checkboxes.first).to_be_checked()
    expect(espece_checkboxes.first).to_be_disabled()
    expect(modal.get_by_text(f"{espece.name} (123456789)", exact=True)).to_be_visible()


def test_can_select_especes_when_there_are_several(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece, other_espece, last_espece = EspeceFactory.create_batch(3)
    veterinaire = VeterinaireFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(1, espece=other_espece)
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(2, espece=last_espece, identifiant="987654321")

    modal = creation_page.open_veterinaire_modal()
    espece_checkboxes = creation_page.get_veterinaire_especes_checkboxes(modal)
    expect(espece_checkboxes).to_have_count(3)
    for index in range(3):
        expect(espece_checkboxes.nth(index)).not_to_be_checked()
        expect(espece_checkboxes.nth(index)).to_be_enabled()

    creation_page.fill_veterinaire(modal, veterinaire)
    modal.get_by_text(other_espece.name, exact=True).click()
    modal.get_by_text(f"{last_espece.name} (987654321)", exact=True).click()
    creation_page.close_veterinaire_modal()
    expect(creation_page.get_veterinaire_card(0)).to_contain_text(f"{last_espece.name} (987654321)")

    creation_page.submit_as_draft()

    saved_veterinaire = EvenementAnimal.objects.get().veterinaires.get()
    assert {(it.espece, it.identifiant) for it in saved_veterinaire.especes_concernees.all()} == {
        (other_espece, None),
        (last_espece, "987654321"),
    }


def test_rows_with_same_espece_can_be_selected_independently(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    poule = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(1, espece=poule, identifiant="123456789")
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(2, espece=poule, identifiant="987654321")

    modal = creation_page.open_veterinaire_modal()
    creation_page.fill_veterinaire(modal, VeterinaireFactory.build())
    modal.get_by_text(f"{poule.name} (987654321)", exact=True).click()
    creation_page.close_veterinaire_modal()
    creation_page.submit_as_draft()

    saved_veterinaire = EvenementAnimal.objects.get().veterinaires.get()
    espece_concernee = saved_veterinaire.especes_concernees.get()
    assert espece_concernee.espece == poule
    assert espece_concernee.identifiant == "987654321"


def test_deleting_selected_espece_updates_veterinaire(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    other_espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(1, espece=other_espece)

    modal = creation_page.open_veterinaire_modal()
    creation_page.fill_veterinaire(modal, VeterinaireFactory.build())
    modal.get_by_text(other_espece.name, exact=True).click()
    creation_page.close_veterinaire_modal()
    card = creation_page.get_veterinaire_card(0)
    expect(card).to_contain_text(other_espece.name)

    creation_page.delete_espece_concernee(1)

    expect(card).not_to_contain_text(other_espece.name)
    expect(card).to_contain_text(espece.name)

    creation_page.submit_as_draft()

    saved_veterinaire = EvenementAnimal.objects.get().veterinaires.get()
    assert saved_veterinaire.especes_concernees.get().espece == espece


def test_selection_is_kept_when_updating_veterinaire(live_server, page: Page):
    evenement = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    selected = EspeceConcerneeFactory(evenement=evenement, espece=evenement.espece)
    not_selected = EspeceConcerneeFactory(evenement=evenement)
    VeterinaireFactory(evenement=evenement, especes_concernees=[selected])
    new_espece = EspeceFactory()

    page.goto(f"{live_server.url}{reverse('sa:evenement-animal-update', kwargs={'pk': evenement.pk})}")
    form_page = EvenementAnimalFormPage(page, live_server.url)
    form_page.add_espece_concernee()
    form_page.fill_espece_concernee(2, espece=new_espece, identifiant="4941034567")

    form_page.get_veterinaire_card(0).locator(".modify-button").click()
    modal = form_page.current_modal
    expect(modal.get_by_label(selected.str_with_identifiant, exact=True)).to_be_checked()
    expect(modal.get_by_label(not_selected.str_with_identifiant, exact=True)).not_to_be_checked()
    new_espece_checkbox = modal.get_by_label(f"{new_espece.name} (4941034567)", exact=True)
    expect(new_espece_checkbox).not_to_be_checked()

    modal.get_by_text(f"{new_espece.name} (4941034567)", exact=True).click()
    form_page.close_veterinaire_modal()
    page.get_by_role("button", name="Enregistrer").first.click()
    expect(page.get_by_text("L’évènement a bien été modifié.")).to_be_visible()

    veterinaire = evenement.veterinaires.get()
    assert {(it.espece, it.identifiant) for it in veterinaire.especes_concernees.all()} == {
        (selected.espece, selected.identifiant),
        (new_espece, "4941034567"),
    }


def test_veterinaire_is_displayed_readonly_on_details_page(live_server, page: Page):
    espece = EspeceFactory()
    evenement = EvenementAnimalFactory(espece=espece)
    espece_concernee = EspeceConcerneeFactory(evenement=evenement, espece=espece, identifiant="123456789")
    veterinaire = VeterinaireFactory(evenement=evenement, especes_concernees=[espece_concernee])

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.nb_veterinaire == 1
    card = details_page.get_veterinaire_card(0)
    card.get_by_text(veterinaire.nom_structure, exact=True).wait_for(state="visible")
    assert veterinaire.get_type_veterinaire_display().upper() in card.inner_text()
    assert f"{espece.name} (123456789)".upper() in card.inner_text().upper()
    assert card.locator(".modify-button").count() == 0
    assert card.get_by_role("button", name="Supprimer").count() == 0

    modal = details_page.open_veterinaire_detail(0)
    assert veterinaire.nom_structure in modal.inner_text()


def test_deleting_evenement_deletes_its_veterinaires(live_server, page: Page, db):
    veterinaire = VeterinaireFactory()
    evenement_id = veterinaire.evenement_id

    EvenementAnimal.objects.get(pk=evenement_id).delete()

    assert Veterinaire.objects.filter(evenement_id=evenement_id).count() == 0

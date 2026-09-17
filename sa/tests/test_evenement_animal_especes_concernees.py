from playwright.sync_api import Page, expect

from sa.models import Espece, EspeceConcernee, EvenementAnimal
from sa.referentiels import situation_unite
from sa.tests.factories import EspeceFactory, EvenementAnimalFactory, MaladieFactory, SituationUniteRegleFactory
from sa.tests.pages import EvenementAnimalDetailsPage, EvenementAnimalFormPage


def _bovin_with_situation_unite_regles():
    """Create "Bovin (Bos taurus)" together with the subset of the tableur combinations
    exercised by the situation-unite tests below (explicit, rather than relying on the
    data migration's rows, since a live_server test flushes the database)."""
    espece, _ = Espece.objects.get_or_create(name="Bovin (Bos taurus)")
    SituationUniteRegleFactory(espece=espece, type_lieu="Abattoir", mode_elevage="", type_production="")
    SituationUniteRegleFactory(
        espece=espece,
        type_lieu="Élevage",
        mode_elevage="Bâtiment ouvert (en partie)",
        type_production="Atelier laitier",
    )
    SituationUniteRegleFactory(
        espece=espece, type_lieu="Élevage", mode_elevage="Bâtiment ouvert (en partie)", type_production="Engraissement"
    )
    return espece


def test_can_create_evenement_animal_with_one_espece_concernee(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_espece_concernee(0, presents="1", morts="2", cas="3", abattus="4", depeuples="5", vaccines="6")
    creation_page.submit_as_draft()

    evenement = EvenementAnimal.objects.get()
    espece_concernee = EspeceConcernee.objects.get()
    assert espece_concernee.evenement == evenement
    assert espece_concernee.espece == espece
    assert espece_concernee.presents == 1
    assert espece_concernee.morts == 2
    assert espece_concernee.cas == 3
    assert espece_concernee.abattus == 4
    assert espece_concernee.depeuples == 5
    assert espece_concernee.vaccines == 6


def test_can_add_and_delete_especes_concernees(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    espece_2 = EspeceFactory()
    espece_3 = EspeceFactory()
    espece_4 = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    creation_page.fill_espece_concernee(0, presents="1")
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(1, espece=espece_2, presents="5")
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(2, espece=espece_3, presents="6")
    creation_page.add_espece_concernee()
    creation_page.fill_espece_concernee(3, espece=espece_4, presents="7")

    assert creation_page.nb_especes_concernees == 4

    creation_page.delete_espece_concernee(2)

    assert creation_page.nb_especes_concernees == 3

    creation_page.submit_as_draft()

    especes_concernees = EspeceConcernee.objects.all()
    assert especes_concernees.count() == 3
    assert set(especes_concernees.values_list("espece", flat=True)) == {espece.pk, espece_2.pk, espece_4.pk}


def test_evenement_animal_show_modal_help(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.page.locator("#especes-concernees .fr-btn--tooltip").click()
    expect(creation_page.page.get_by_text("Aide au remplissage", exact=True)).to_be_visible()


def test_situation_unite_button_disabled_without_espece(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece, _ = Espece.objects.get_or_create(name="Bovin (Bos taurus)")

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.add_espece_concernee()

    expect(creation_page.situation_unite_button(1)).to_be_disabled()


def test_situation_unite_button_disabled_for_species_absent_from_tableur(
    live_server, mocked_authentification_user, page: Page
):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    assert espece.name not in situation_unite.build_tree()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    expect(creation_page.situation_unite_button(0)).to_be_disabled()


def test_situation_unite_full_workflow(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = _bovin_with_situation_unite_regles()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    expect(creation_page.situation_unite_button(0)).to_be_enabled()

    modal = creation_page.open_situation_unite_modal(0)
    expect(modal.locator('select[id$="-mode_elevage"]')).to_be_hidden()

    modal.locator('select[id$="-type_lieu"]').select_option("Élevage")
    expect(modal.locator('select[id$="-mode_elevage"]')).to_be_visible()
    expect(modal.locator('select[id$="-type_production"]')).to_be_hidden()

    modal.locator('select[id$="-mode_elevage"]').select_option("Bâtiment ouvert (en partie)")
    expect(modal.locator('select[id$="-type_production"]')).to_be_visible()

    modal.locator('select[id$="-type_production"]').select_option("Atelier laitier")

    creation_page.save_situation_unite(0)

    summary = creation_page.get_situation_unite_summary(0)
    assert "Élevage" in summary
    assert "Bâtiment ouvert (en partie)" in summary
    assert "Atelier laitier" in summary
    expect(creation_page.situation_unite_button(0)).to_be_hidden()

    creation_page.edit_situation_unite(0, type_production="Engraissement")
    summary = creation_page.get_situation_unite_summary(0)
    assert "Engraissement" in summary

    creation_page.submit_as_draft()

    espece_concernee = EspeceConcernee.objects.get()
    assert espece_concernee.type_lieu == "Élevage"
    assert espece_concernee.mode_elevage == "Bâtiment ouvert (en partie)"
    assert espece_concernee.type_production == "Engraissement"
    assert espece_concernee.type_elevage == ""

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(EvenementAnimal.objects.get())
    values = details_page.get_especes_concernees_values()
    assert "Élevage" in values[0][2]
    assert "Engraissement" in values[0][2]


def test_situation_unite_options_are_filtered_by_species_and_path(
    live_server, mocked_authentification_user, page: Page
):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = _bovin_with_situation_unite_regles()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    modal = creation_page.open_situation_unite_modal(0)

    type_lieu_options = modal.locator('select[id$="-type_lieu"] option').all_inner_texts()
    assert "Basse-cour" not in type_lieu_options
    assert "Élevage" in type_lieu_options
    assert "Abattoir" in type_lieu_options

    modal.locator('select[id$="-type_lieu"]').select_option("Élevage")
    mode_elevage_options = modal.locator('select[id$="-mode_elevage"] option').all_inner_texts()
    assert "Élevage en bâtiment" not in mode_elevage_options
    assert "Bâtiment ouvert (en partie)" in mode_elevage_options


def test_situation_unite_leaf_without_children_needs_no_further_level(
    live_server, mocked_authentification_user, page: Page
):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = _bovin_with_situation_unite_regles()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    modal = creation_page.open_situation_unite_modal(0)
    modal.locator('select[id$="-type_lieu"]').select_option("Abattoir")
    creation_page.save_situation_unite(0)

    summary = creation_page.get_situation_unite_summary(0)
    assert summary.strip() == "Abattoir\nModifier"


def test_situation_unite_cancel_discards_changes(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = _bovin_with_situation_unite_regles()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    modal = creation_page.open_situation_unite_modal(0)
    modal.locator('select[id$="-type_lieu"]').select_option("Abattoir")
    creation_page.cancel_situation_unite(0)

    expect(creation_page.situation_unite_button(0)).to_be_visible()
    expect(creation_page.situation_unite_button(0)).to_be_enabled()

    # Fill an unrelated field so the (otherwise still "unchanged") row is actually saved.
    creation_page.fill_espece_concernee(0, presents="1")
    creation_page.submit_as_draft()
    espece_concernee = EspeceConcernee.objects.get()
    assert espece_concernee.type_lieu == ""

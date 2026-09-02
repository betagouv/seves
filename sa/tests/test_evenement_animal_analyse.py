from playwright.sync_api import Page

from sa.models import Analyse, EvenementAnimal
from sa.tests.factories import (
    AnalyseFactory,
    EspeceFactory,
    EvenementAnimalFactory,
    LaboratoireFactory,
    MaladieFactory,
    MethodeAnalyseFactory,
)
from sa.tests.pages import EvenementAnimalDetailsPage, EvenementAnimalFormPage

FIELDS_TO_EXCLUDE_ANALYSE = ["_state", "id", "evenement_id"]


def test_can_add_analyse(live_server, page: Page, assert_models_are_equal):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    laboratoire = LaboratoireFactory()
    methode = MethodeAnalyseFactory(laboratoires=[laboratoire])
    analyse = AnalyseFactory.build(maladie=maladie, laboratoire=laboratoire, methode=methode)

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.add_analyse(analyse)

    assert creation_page.nb_analyse == 1

    creation_page.submit_as_draft()

    saved_analyse = EvenementAnimal.objects.get().analyses.get()
    assert_models_are_equal(analyse, saved_analyse, to_exclude=FIELDS_TO_EXCLUDE_ANALYSE)


def test_can_add_and_cancel_analyse(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    laboratoire = LaboratoireFactory()
    methode = MethodeAnalyseFactory(laboratoires=[laboratoire])
    analyse = AnalyseFactory.build(maladie=maladie, laboratoire=laboratoire, methode=methode)

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    # Open modal, fill and delete
    creation_page.add_analyse(analyse)
    creation_page.delete_analyse(0)

    # Open modal and cancel
    creation_page.open_analyse_modal()
    creation_page.current_modal.get_by_role("button", name="Annuler").click()
    creation_page.current_modal.wait_for(state="hidden", timeout=2_000)

    creation_page.submit_as_draft()
    assert EvenementAnimal.objects.get().analyses.count() == 0


def test_add_button_is_disabled_after_five_analyses(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    laboratoire = LaboratoireFactory()
    methode = MethodeAnalyseFactory(laboratoires=[laboratoire])

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    for _ in range(5):
        analyse = AnalyseFactory.build(maladie=maladie, laboratoire=laboratoire, methode=methode)
        creation_page.add_analyse(analyse)

    assert creation_page.nb_analyse == 5
    assert creation_page.add_analyse_button.is_disabled()

    creation_page.submit_as_draft()
    assert EvenementAnimal.objects.get().analyses.count() == 5


def test_methode_options_are_filtered_by_selected_laboratoire(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    laboratoire_1 = LaboratoireFactory()
    laboratoire_2 = LaboratoireFactory()
    methode_1 = MethodeAnalyseFactory(laboratoires=[laboratoire_1])
    MethodeAnalyseFactory(laboratoires=[laboratoire_2])

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    modal = creation_page.open_analyse_modal()
    methode_select = modal.locator('[id$="-methode"]')
    assert methode_select.is_disabled()

    modal.locator('[id$="-laboratoire"]').select_option(str(laboratoire_1.pk))
    assert not methode_select.is_disabled()
    assert methode_select.locator("option").count() == 2  # placeholder + methode_1
    methode_select.select_option(str(methode_1.pk))

    modal.locator('[id$="-laboratoire"]').select_option(str(laboratoire_2.pk))
    assert methode_select.locator("option").count() == 2  # placeholder + methode_2
    assert methode_select.input_value() == ""


def test_analyse_is_displayed_readonly_on_details_page(live_server, page: Page):
    laboratoire = LaboratoireFactory(laboratoire_type="lnr")
    methode = MethodeAnalyseFactory(laboratoires=[laboratoire])
    analyse = AnalyseFactory(laboratoire=laboratoire, methode=methode, resultat="detecte")
    evenement = analyse.evenement

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.nb_analyse == 1
    card = details_page.get_analyse_card(0)
    card.get_by_text(analyse.maladie.name, exact=True).wait_for(state="visible")
    assert laboratoire.name in card.inner_text()
    assert "LNR" in card.inner_text()
    assert card.locator(".modify-button").count() == 0
    assert card.get_by_role("button", name="Supprimer").count() == 0

    modal = details_page.open_analyse_detail(0)
    assert methode.libelle in modal.inner_text()


def test_deleting_evenement_deletes_its_analyses(live_server, page: Page, db):
    analyse = AnalyseFactory()
    evenement_id = analyse.evenement_id

    EvenementAnimal.objects.get(pk=evenement_id).delete()

    assert Analyse.objects.filter(evenement_id=evenement_id).count() == 0

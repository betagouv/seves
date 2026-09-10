from playwright.sync_api import Page, expect

from sa.models import EspeceConcernee, EvenementAnimal
from sa.tests.factories import EspeceFactory, EvenementAnimalFactory, MaladieFactory
from sa.tests.pages import EvenementAnimalFormPage


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

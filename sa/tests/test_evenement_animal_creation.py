from playwright.sync_api import Page

from sa.models import EvenementAnimal
from sa.tests.factories import EspeceFactory, EvenementAnimalFactory, MaladieFactory
from sa.tests.pages import EvenementAnimalFormPage, EvenementListPage


def test_can_create_evenement_animal_with_required_fields_only_from_list_page(
    live_server, mocked_authentification_user, page: Page
):
    input_data = EvenementAnimalFactory()
    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.open_pre_creation_form()
    list_page.fill_pre_creation_form(input_data)

    list_page.page.wait_for_url("**/sa/evenement-animal/creation**")
    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.fill_required_fields(input_data)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.maladie == input_data.maladie
    assert evenement_produit.espece == input_data.espece
    assert evenement_produit.statut_animal == input_data.statut_animal
    assert evenement_produit.statut_evenement == input_data.statut_evenement
    assert evenement_produit.date_statut_changed == input_data.date_statut_changed


def test_can_create_evenement_animal_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.maladie == maladie
    assert evenement_produit.espece == espece
    assert evenement_produit.statut_animal == input_data.statut_animal
    assert evenement_produit.statut_evenement == input_data.statut_evenement
    assert evenement_produit.date_statut_changed == input_data.date_statut_changed

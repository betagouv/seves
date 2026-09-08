from playwright.sync_api import Page, expect

from core.factories import StructureFactory
from sa.tests.factories import EspeceFactory, EvenementAnimalFactory, MaladieFactory
from sa.tests.pages import EvenementListPage
from seves import settings


def test_search_form_have_all_fields(live_server, page: Page):
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_role("heading", name="Rechercher un événement")).to_be_visible()
    expect(search_page.annee_field).to_be_visible()
    expect(search_page.numero_field).to_be_visible()
    expect(search_page.maladie_field).to_be_visible()
    expect(search_page.maladie_field).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(search_page.espece_field).to_be_visible()
    expect(search_page.etat_field).to_be_visible()
    expect(page.get_by_role("button", name="Effacer", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


def test_reset_button_clears_form(live_server, page: Page):
    maladie = MaladieFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.annee_field.fill("2026")
    search_page.maladie_field.select_option(str(maladie.pk))

    search_page.reset_search()

    expect(search_page.annee_field).to_be_empty()
    expect(search_page.maladie_field).to_have_value("")


def test_evenement_animal_list_displays_events_and_links_to_details(live_server, page: Page):
    evenement = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    row = search_page.row(evenement.numero)
    expect(row).to_be_visible()
    expect(row).to_contain_text(evenement.maladie.name)
    expect(row).to_contain_text(evenement.espece.name)
    expect(row).to_contain_text(evenement.get_statut_evenement_display())
    expect(row).to_contain_text(evenement.get_etat_display())

    row.get_by_role("link", name=evenement.numero, exact=True).click()
    page.wait_for_url(f"**{evenement.get_absolute_url()}")


def test_evenement_animal_list_compteur(live_server, page: Page):
    EvenementAnimalFactory.create_batch(3)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_text("3 sur un total de 3")).to_be_visible()


def test_evenement_animal_list_filter_by_maladie(live_server, page: Page):
    maladie = MaladieFactory()
    matching = EvenementAnimalFactory(maladie=maladie)
    other = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.maladie_field.select_option(str(maladie.pk))
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_espece(live_server, page: Page):
    espece = EspeceFactory()
    matching = EvenementAnimalFactory(espece=espece)
    other = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.espece_field.select_option(str(espece.pk))
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_cant_see_draft_of_other_structure(live_server, page: Page):
    evenement = EvenementAnimalFactory()
    evenement.createur = StructureFactory()
    evenement.save()
    assert evenement.is_draft is True

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_text("0 sur un total de 0")).to_be_visible()

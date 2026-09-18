from django.conf import settings
from playwright.sync_api import Page, expect

from sa.models import EvenementAnimal
from sa.tests.factories import (
    AcarapioseFactory,
    EspeceFactory,
    EvenementAnimalFactory,
    TuberculoseFactory,
)
from sa.tests.pages import EvenementAnimalFormPage


def test_typage_block_shows_free_text_only(live_server, page: Page):
    maladie = AcarapioseFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    expect(creation_page.typage_champ_libre).to_be_visible()
    expect(creation_page.page.get_by_text("Typage complémentaire", exact=True)).to_be_visible()
    expect(creation_page.typage_niveau_2_select).to_have_count(0)
    expect(creation_page.typage_niveau_3_select).to_have_count(0)


def test_typage_block_shows_three_fields(live_server, page: Page):
    maladie = TuberculoseFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    block = creation_page.page.locator("#typage")

    expect(block.get_by_text("Espèce", exact=True)).to_be_visible()
    expect(block.get_by_text("Spoligotype", exact=True)).to_be_visible()
    expect(block.get_by_text("Autre spoligotype", exact=True)).to_be_visible()

    niveau_2_texts = [
        option.inner_text() for option in creation_page.typage_niveau_2.locator("option").element_handles()
    ]
    assert niveau_2_texts == [
        settings.SELECT_EMPTY_CHOICE,
        "Mycobacterium bovis",
        "Mycobacterium caprae",
        "Mycobacterium tuberculosis",
    ]


def test_typage_niveau_3_options_follow_selected_niveau_2(live_server, page: Page):
    maladie = TuberculoseFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    expect(creation_page.typage_niveau_3_select).to_be_disabled()

    creation_page.typage_niveau_2_select.select_option("Mycobacterium bovis")
    expect(creation_page.typage_niveau_3_select).to_be_enabled()
    visible_texts = [o.inner_text() for o in creation_page.typage_niveau_3_select.locator("option").element_handles()]
    assert len(visible_texts) == 44

    creation_page.typage_niveau_2_select.select_option("Mycobacterium caprae")
    expect(creation_page.typage_niveau_3_select).to_be_disabled()


def test_can_create_evenement_animal_with_typage_block(live_server, mocked_authentification_user, page: Page):
    maladie = TuberculoseFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build(maladie=maladie)

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.typage_niveau_2_select.select_option("Mycobacterium bovis")
    creation_page.typage_niveau_3_select.select_option("SB0263")
    creation_page.typage_champ_libre.fill("Test")
    creation_page.submit_as_draft()

    evenement = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    assert evenement.typage.valeur_niveau_2 == "Mycobacterium bovis"
    assert evenement.typage.valeur_niveau_3 == "SB0263"
    assert evenement.typage_champ_libre == "Test"

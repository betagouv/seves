from django.conf import settings
from playwright.sync_api import Page, expect
import pytest

from sa.models import EvenementAnimal, Typage
from sa.tests.factories import (
    AcarapioseFactory,
    EspeceFactory,
    EvenementAnimalFactory,
    TuberculoseFactory,
)
from sa.tests.pages import EvenementAnimalFormPage


@pytest.fixture
def reset_typage_tuberculose():
    Typage.objects.all().delete()
    typages = [
        ("Mycobacterium bovis", "A/SB0999"),
        ("Mycobacterium bovis", "BCG / SB0120"),
        ("Mycobacterium bovis", "F001 / SB0840"),
        ("Mycobacterium bovis", "F003 / SB0822"),
        ("Mycobacterium bovis", "F004 / SB0818"),
        ("Mycobacterium bovis", "F005 / SB0826"),
        ("Mycobacterium bovis", "F006 / SB0089"),
        ("Mycobacterium bovis", "F007 / SB0821"),
        ("Mycobacterium bovis", "F008 / SB0836"),
        ("Mycobacterium bovis", "F009 / SB0853"),
        ("Mycobacterium bovis", "F010 / SB0829"),
        ("Mycobacterium bovis", "F011 / SB0828"),
        ("Mycobacterium bovis", "F013 / SB0820"),
        ("Mycobacterium bovis", "F015 / SB0832"),
        ("Mycobacterium bovis", "F018 / SB0852"),
        ("Mycobacterium bovis", "F019 / SB0861"),
        ("Mycobacterium bovis", "F022 / SB0819"),
        ("Mycobacterium bovis", "F023 / SB0827"),
        ("Mycobacterium bovis", "F029 / SB0837"),
        ("Mycobacterium bovis", "F032 / SB0867"),
        ("Mycobacterium bovis", "F037 / SB0849"),
        ("Mycobacterium bovis", "F041 / SB0823"),
        ("Mycobacterium bovis", "F043 / SB0824"),
        ("Mycobacterium bovis", "F053 / SB0946"),
        ("Mycobacterium bovis", "F057 / SB0878"),
        ("Mycobacterium bovis", "F061 / SB0825"),
        ("Mycobacterium bovis", "F067 / SB0875"),
        ("Mycobacterium bovis", "F070 / SB0295"),
        ("Mycobacterium bovis", "F072 / SB0928"),
        ("Mycobacterium bovis", "F077 / SB0866"),
        ("Mycobacterium bovis", "F089 / SB0845"),
        ("Mycobacterium bovis", "F096 / SB0833"),
        ("Mycobacterium bovis", "F100 / SB0851"),
        ("Mycobacterium bovis", "F105 / SB0948"),
        ("Mycobacterium bovis", "F110 / SB0885"),
        ("Mycobacterium bovis", "F135 / SB0870"),
        ("Mycobacterium bovis", "F140 / SB0843"),
        ("Mycobacterium bovis", "GB20 / SB0145"),
        ("Mycobacterium bovis", "GB21 / SB0130"),
        ("Mycobacterium bovis", "GB35 / SB0134"),
        ("Mycobacterium bovis", "GB54 / SB0121"),
        ("Mycobacterium bovis", "GB55 / SB0418"),
        ("Mycobacterium bovis", "GB9 / SB0140"),
        ("Mycobacterium bovis", "SB0243"),
        ("Mycobacterium bovis", "SB0263"),
        ("Mycobacterium bovis", "SB1095"),
        ("Mycobacterium bovis", "SB2202"),
        ("Mycobacterium bovis", "SB2232"),
        ("Mycobacterium bovis", "SB2539"),
        ("Mycobacterium caprae", ""),
        ("Mycobacterium tuberculosis", ""),
    ]
    maladie = TuberculoseFactory()
    for valeur_niveau_2, valeur_niveau_3 in typages:
        Typage.objects.get_or_create(
            maladie=maladie,
            valeur_niveau_2=valeur_niveau_2,
            valeur_niveau_3=valeur_niveau_3,
        )
    return maladie


def test_typage_block_shows_free_text_only(live_server, page: Page):
    maladie = AcarapioseFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    expect(creation_page.typage_champ_libre).to_be_visible()
    expect(creation_page.page.get_by_text("Typage complémentaire", exact=True)).to_be_visible()
    expect(creation_page.typage_niveau_2).to_have_count(0)
    expect(creation_page.typage_niveau_3).to_have_count(0)


def test_typage_block_shows_three_fields(live_server, page: Page, reset_typage_tuberculose):
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(reset_typage_tuberculose, espece, input_data.statut_animal)

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


def test_typage_niveau_3_options_follow_selected_niveau_2(live_server, page: Page, reset_typage_tuberculose):
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(reset_typage_tuberculose, espece, input_data.statut_animal)

    expect(creation_page.typage_niveau_3).to_be_disabled()

    creation_page.typage_niveau_2.select_option("Mycobacterium bovis")
    expect(creation_page.typage_niveau_3).to_be_enabled()
    visible_texts = [o.inner_text() for o in creation_page.typage_niveau_3.locator("option").element_handles()]
    assert len(visible_texts) == 50

    creation_page.typage_niveau_2.select_option("Mycobacterium caprae")
    expect(creation_page.typage_niveau_3).to_be_disabled()


def test_can_create_evenement_animal_with_typage_block(
    live_server, mocked_authentification_user, page: Page, reset_typage_tuberculose
):
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build(maladie=reset_typage_tuberculose)

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(reset_typage_tuberculose, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.typage_niveau_2.select_option("Mycobacterium bovis")
    creation_page.typage_niveau_3.select_option("SB0263")
    creation_page.typage_champ_libre.fill("Test")
    creation_page.submit_as_draft()

    evenement = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    assert evenement.typage.valeur_niveau_2 == "Mycobacterium bovis"
    assert evenement.typage.valeur_niveau_3 == "SB0263"
    assert evenement.typage_champ_libre == "Test"

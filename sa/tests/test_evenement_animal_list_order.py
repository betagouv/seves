from playwright.sync_api import Page
import pytest

from sa.tests.factories import EvenementAnimalFactory, MaladieFactory


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_2", "evenement_3", "evenement_1"]),
        ("desc", ["evenement_1", "evenement_3", "evenement_2"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_numero_evenement(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementAnimalFactory(numero_annee=2026, numero_evenement=3),
        "evenement_2": EvenementAnimalFactory(numero_annee=2026, numero_evenement=1),
        "evenement_3": EvenementAnimalFactory(numero_annee=2026, numero_evenement=2),
    }
    page.goto(url_builder_for_list_ordering("numero_evenement", direction, "sa:evenement-liste"))
    page.get_by_role("link", name="Événement", exact=True).click()
    assert_events_order(page, evenements, expected_order, column=1)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_maladie_a", "evenement_maladie_b", "evenement_maladie_c"]),
        ("desc", ["evenement_maladie_c", "evenement_maladie_b", "evenement_maladie_a"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_maladie(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_maladie_a": EvenementAnimalFactory(maladie=MaladieFactory(name="Anthrax")),
        "evenement_maladie_b": EvenementAnimalFactory(maladie=MaladieFactory(name="Brucellose")),
        "evenement_maladie_c": EvenementAnimalFactory(maladie=MaladieFactory(name="Charbon")),
    }
    page.goto(url_builder_for_list_ordering("maladie", direction, "sa:evenement-liste"))
    page.get_by_role("link", name="Maladie").click()
    assert_events_order(page, evenements, expected_order, column=1)

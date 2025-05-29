from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import Page

from core.factories import StructureFactory
from core.models import Visibilite
from sv.factories import FicheDetectionFactory, EvenementFactory, FicheZoneFactory
from sv.models import Evenement, Etat


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_2", "evenement_3", "evenement_1"]),
        ("desc", ["evenement_3", "evenement_1", "evenement_2"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_ac_notified(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(is_ac_notified=True),
        "evenement_2": EvenementFactory(is_ac_notified=False),
        "evenement_3": EvenementFactory(is_ac_notified=True),
    }
    page.goto(url_builder_for_list_ordering("ac_notified", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Notifié AC").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_3", "evenement_1", "evenement_2"]),
        ("desc", ["evenement_2", "evenement_1", "evenement_3"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_numero_evenement(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(numero_annee=2025, numero_evenement=2),
        "evenement_2": EvenementFactory(numero_annee=2025, numero_evenement=3),
        "evenement_3": EvenementFactory(numero_annee=2025, numero_evenement=1),
    }
    page.goto(url_builder_for_list_ordering("numero_evenement", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Évènement", exact=True).click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_1", "evenement_3", "evenement_2"]),
        ("desc", ["evenement_2", "evenement_3", "evenement_1"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_organisme_nuisible(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(organisme_nuisible__libelle_court="A"),
        "evenement_2": EvenementFactory(organisme_nuisible__libelle_court="C"),
        "evenement_3": EvenementFactory(organisme_nuisible__libelle_court="B"),
    }
    page.goto(url_builder_for_list_ordering("organisme", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Organisme nuisible").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_1", "evenement_3", "evenement_2"]),
        ("desc", ["evenement_2", "evenement_3", "evenement_1"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_date_creation(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(date_creation=timezone.make_aware(datetime(2023, 1, 1))),
        "evenement_2": EvenementFactory(date_creation=timezone.make_aware(datetime(2023, 3, 1))),
        "evenement_3": EvenementFactory(date_creation=timezone.make_aware(datetime(2023, 2, 1))),
    }
    page.goto(url_builder_for_list_ordering("creation", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Création").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_1", "evenement_3", "evenement_2"]),
        ("desc", ["evenement_2", "evenement_3", "evenement_1"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_date_derniere_mise_a_jour(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    Evenement._meta.get_field("date_derniere_mise_a_jour").auto_now = False
    evenements = {
        "evenement_1": EvenementFactory(date_derniere_mise_a_jour=timezone.make_aware(datetime(2025, 1, 1))),
        "evenement_2": EvenementFactory(date_derniere_mise_a_jour=timezone.make_aware(datetime(2025, 3, 1))),
        "evenement_3": EvenementFactory(date_derniere_mise_a_jour=timezone.make_aware(datetime(2025, 2, 1))),
    }
    page.goto(url_builder_for_list_ordering("maj", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Dernière MAJ descripteurs").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_1", "evenement_3", "evenement_2"]),
        ("desc", ["evenement_2", "evenement_3", "evenement_1"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_createur(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(createur=StructureFactory(libelle="A"), visibilite=Visibilite.NATIONALE),
        "evenement_2": EvenementFactory(createur=StructureFactory(libelle="C"), visibilite=Visibilite.NATIONALE),
        "evenement_3": EvenementFactory(createur=StructureFactory(libelle="B"), visibilite=Visibilite.NATIONALE),
    }
    page.goto(url_builder_for_list_ordering("createur", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Créateur").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_2", "evenement_3", "evenement_1"]),
        ("desc", ["evenement_1", "evenement_3", "evenement_2"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_etat(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(etat=Etat.NOUVEAU),
        "evenement_2": EvenementFactory(etat=Etat.CLOTURE),
        "evenement_3": EvenementFactory(etat=Etat.EN_COURS),
    }
    page.goto(url_builder_for_list_ordering("etat", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="État").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_1", "evenement_3", "evenement_2"]),
        ("desc", ["evenement_2", "evenement_3", "evenement_1"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_visibilite(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenement_1 = EvenementFactory()
    structure = StructureFactory()
    evenement_1.allowed_structures.add(structure)
    evenement_1.visibilite = Visibilite.LIMITEE
    evenement_1.save()
    evenements = {
        "evenement_1": evenement_1,
        "evenement_2": EvenementFactory(visibilite=Visibilite.NATIONALE),
        "evenement_3": EvenementFactory(visibilite=Visibilite.LOCALE),
    }
    page.goto(url_builder_for_list_ordering("visibilite", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Visibilité").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_3", "evenement_1", "evenement_2"]),
        ("desc", ["evenement_2", "evenement_1", "evenement_3"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_detections(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(),
        "evenement_2": EvenementFactory(),
        "evenement_3": EvenementFactory(),
    }
    FicheDetectionFactory.create_batch(2, evenement=evenements["evenement_1"])
    FicheDetectionFactory.create_batch(3, evenement=evenements["evenement_2"])
    FicheDetectionFactory.create_batch(1, evenement=evenements["evenement_3"])
    page.goto(url_builder_for_list_ordering("detections", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Détections").click()
    assert_events_order(page, evenements, expected_order)


@pytest.mark.parametrize(
    "direction,expected_order",
    [
        ("asc", ["evenement_2", "evenement_1"]),
        ("desc", ["evenement_1", "evenement_2"]),
    ],
    ids=["asc", "desc"],
)
def test_order_by_zone(
    live_server, page: Page, url_builder_for_list_ordering, assert_events_order, direction, expected_order
):
    evenements = {
        "evenement_1": EvenementFactory(),
        "evenement_2": EvenementFactory(fiche_zone_delimitee=FicheZoneFactory()),
    }
    page.goto(url_builder_for_list_ordering("zone", direction, "sv:evenement-liste"))
    page.get_by_role("link", name="Zone").click()
    assert_events_order(page, evenements, expected_order)


def test_order_by_with_bad_parameters_order_by_date_derniere_mise_a_jour_desc(
    live_server, page: Page, assert_events_order
):
    Evenement._meta.get_field("date_derniere_mise_a_jour").auto_now = False
    evenements = {
        "evenement_1": EvenementFactory(date_derniere_mise_a_jour=timezone.make_aware(datetime(2025, 2, 1))),
        "evenement_2": EvenementFactory(date_derniere_mise_a_jour=timezone.make_aware(datetime(2025, 3, 1))),
        "evenement_3": EvenementFactory(date_derniere_mise_a_jour=timezone.make_aware(datetime(2025, 1, 1))),
    }
    expected_order = ["evenement_2", "evenement_1", "evenement_3"]
    page.goto(
        f"{live_server.url}{reverse('sv:evenement-liste')}?order_by=bad_order_by_value&order_dir=bad_order_dir_value"
    )
    assert_events_order(page, evenements, expected_order)

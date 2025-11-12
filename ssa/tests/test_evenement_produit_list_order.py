from datetime import datetime

import pytest
from django.utils import timezone
from playwright.sync_api import Page

from core.factories import StructureFactory
from core.mixins import WithEtatMixin
from ssa.factories import EvenementProduitFactory


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
        "evenement_1": EvenementProduitFactory(numero_annee=2025, numero_evenement=2),
        "evenement_2": EvenementProduitFactory(numero_annee=2025, numero_evenement=3),
        "evenement_3": EvenementProduitFactory(numero_annee=2025, numero_evenement=1),
    }
    page.goto(url_builder_for_list_ordering("numero_evenement", direction, "ssa:evenement-produit-liste"))
    page.get_by_role("link", name="N°", exact=True).click()
    assert_events_order(page, evenements, expected_order, 1)


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
        "evenement_1": EvenementProduitFactory(date_creation=timezone.make_aware(datetime(2023, 1, 1))),
        "evenement_2": EvenementProduitFactory(date_creation=timezone.make_aware(datetime(2023, 3, 1))),
        "evenement_3": EvenementProduitFactory(date_creation=timezone.make_aware(datetime(2023, 2, 1))),
    }
    page.goto(url_builder_for_list_ordering("creation", direction, "ssa:evenement-produit-liste"))
    page.get_by_role("link", name="Création").click()
    assert_events_order(page, evenements, expected_order, 1)


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
        "evenement_1": EvenementProduitFactory(
            createur=StructureFactory(libelle="A"), etat=WithEtatMixin.Etat.EN_COURS
        ),
        "evenement_2": EvenementProduitFactory(
            createur=StructureFactory(libelle="C"), etat=WithEtatMixin.Etat.EN_COURS
        ),
        "evenement_3": EvenementProduitFactory(
            createur=StructureFactory(libelle="B"), etat=WithEtatMixin.Etat.EN_COURS
        ),
    }
    page.goto(url_builder_for_list_ordering("createur", direction, "ssa:evenement-produit-liste"))
    page.get_by_role("link", name="Créateur").click()
    assert_events_order(page, evenements, expected_order, 1)


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
        "evenement_1": EvenementProduitFactory(etat=WithEtatMixin.Etat.EN_COURS),
        "evenement_2": EvenementProduitFactory(etat=WithEtatMixin.Etat.BROUILLON),
        "evenement_3": EvenementProduitFactory(etat=WithEtatMixin.Etat.CLOTURE),
    }
    page.goto(url_builder_for_list_ordering("etat", direction, "ssa:evenement-produit-liste"))
    page.get_by_role("link", name="État").click()
    assert_events_order(page, evenements, expected_order, 1)

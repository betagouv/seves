from django.urls import reverse
from playwright.sync_api import Page, expect

from sv.factories import FicheDetectionFactory, LieuFactory


def test_commune_column_with_multiple_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="Marseille")

    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name="Paris, Lyon, Marseille")).to_be_visible()


def test_commune_column_with_some_empty_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name="Paris, Lyon")).to_be_visible()


def test_commune_column_with_empty_commune(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name="nc.")).to_be_visible()


def test_commune_column_without_lieu(live_server, page: Page):
    FicheDetectionFactory()
    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name="nc.")).to_be_visible()
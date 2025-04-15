from django.urls import reverse
from playwright.sync_api import Page, expect

from sv.factories import FicheDetectionFactory, LieuFactory, EvenementFactory


def test_commune_column_with_multiple_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="Marseille")

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("Paris, Lyon, Marseille", exact=True)).to_be_visible()


def test_commune_column_with_some_empty_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("Paris, Lyon", exact=True)).to_be_visible()


def test_commune_column_with_empty_commune(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("nc.", exact=True)).to_be_visible()


def test_commune_column_without_lieu(live_server, page: Page):
    FicheDetectionFactory()
    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("nc.", exact=True)).to_be_visible()


def test_duplicate_commune_appears_only_once(live_server, page: Page):
    e = EvenementFactory()
    LieuFactory(commune="La Rochelle", fiche_detection__evenement=e)
    LieuFactory(commune="La Rochelle", fiche_detection__evenement=e)
    LieuFactory(commune="Bordeaux", fiche_detection__evenement=e)

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")

    expect(page.get_by_text("Bordeaux, La Rochelle", exact=True)).to_be_visible()

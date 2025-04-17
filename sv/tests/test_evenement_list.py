from django.urls import reverse
from playwright.sync_api import Page, expect

from sv.factories import FicheDetectionFactory, LieuFactory, EvenementFactory, FicheZoneFactory


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


def test_list_ordered_by_most_recent_date_derniere_modification(live_server, page: Page):
    evenement1 = FicheDetectionFactory().evenement
    evenement2 = EvenementFactory(fiche_zone_delimitee=FicheZoneFactory())
    evenement3 = FicheDetectionFactory().evenement

    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")

    assert page.text_content(".evenements__list-row:nth-child(1) td:nth-child(2)").strip() == evenement3.numero
    assert page.text_content(".evenements__list-row:nth-child(2) td:nth-child(2)").strip() == evenement2.numero
    assert page.text_content(".evenements__list-row:nth-child(3) td:nth-child(2)").strip() == evenement1.numero

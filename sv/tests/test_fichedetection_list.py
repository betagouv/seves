import re

from django.urls import reverse
from playwright.sync_api import Page, expect

from sv.factories import FicheDetectionFactory, LieuFactory, EvenementFactory, FicheZoneFactory


def test_commune_column_with_multiple_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="Marseille")

    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_text("Paris, Lyon, Marseille", exact=True)).to_be_visible()


def test_commune_column_with_some_empty_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_text("Paris, Lyon", exact=True)).to_be_visible()


def test_commune_column_with_empty_commune(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_text("nc.", exact=True)).to_be_visible()


def test_commune_column_without_lieu(live_server, page: Page):
    FicheDetectionFactory()
    page.goto(f"{live_server}{reverse('fiche-liste')}")
    expect(page.get_by_text("nc.", exact=True)).to_be_visible()


def test_click_on_detection_in_table_redirects_to_detection_tab(live_server, page):
    evenement = EvenementFactory()
    _, detection_2, _ = FicheDetectionFactory.create_batch(3, evenement=evenement)

    page.goto(f"{live_server}{reverse('fiche-liste')}")
    page.get_by_test_id(f"{detection_2.numero}").click()

    expect(page.get_by_role("tab", name=f"{detection_2.numero}")).to_be_visible()
    expect(page.get_by_role("tab", name=f"{detection_2.numero}")).to_have_class(re.compile(r"(^|\s)selected($|\s)"))


def test_click_on_zone_in_table_redirects_to_zone_tab(live_server, page):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)

    page.goto(f"{live_server}{reverse('fiche-liste')}?type_fiche=zone")
    page.get_by_role("link", name=f"{evenement.numero}").click()

    expect(page.get_by_role("tab", name="Zone")).to_have_count(1)
    expect(page.get_by_text("Zone tampon")).to_be_visible()

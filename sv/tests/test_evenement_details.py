from playwright.sync_api import expect, Page

from core.models import Visibilite
from sv.factories import EvenementFactory, FicheZoneFactory, FicheDetectionFactory


def test_cant_add_zone_if_already_one(live_server, page: Page):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("Ajouter une zone", exact=True)).to_be_disabled()


def test_can_publish_evenement(live_server, page: Page):
    evenement = EvenementFactory(visibilite=Visibilite.BROUILLON)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    publish_btn = page.get_by_text("Publier l'événement", exact=True)
    expect(publish_btn).to_be_enabled()
    publish_btn.click()
    expect(page.get_by_text("La visibilité de l'évenement a bien été modifiée.")).to_be_visible()

    page.get_by_role("button", name="Actions").click()
    publish_btn = page.get_by_text("Publier l'événement", exact=True)
    expect(publish_btn).not_to_be_visible()


def test_detail_synthese_switch(live_server, page):
    evenement = EvenementFactory()
    FicheDetectionFactory(evenement=evenement)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    detail_radio = page.locator("#detail-btn")
    expect(detail_radio).to_be_checked()
    detail_content = page.locator("#detail-content")
    expect(detail_content).to_be_visible()

    synthese_radio = page.locator("#synthese-btn")
    synthese_radio.click(force=True)
    expect(detail_content).to_be_hidden()

    detail_radio.click(force=True)
    expect(detail_content).to_be_visible()

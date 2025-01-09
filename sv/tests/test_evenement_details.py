from playwright.sync_api import expect, Page

from core.models import Visibilite
from sv.factories import EvenementFactory, FicheZoneFactory


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

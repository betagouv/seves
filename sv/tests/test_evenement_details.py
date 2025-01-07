from playwright.sync_api import expect, Page

from sv.factories import EvenementFactory, FicheZoneFactory


def test_cant_add_zone_if_alreay_one(live_server, page: Page):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("Ajouter une zone", exact=True)).to_be_disabled()

from playwright.sync_api import Page, expect

from sv.factories import EvenementFactory, FicheDetectionFactory, FicheZoneFactory, ZoneInfesteeFactory


def test_fichezonedelimitee_with_zoneinfestee_detail(live_server, page: Page, mocked_authentification_user):
    fiche_zone_delimitee = FicheZoneFactory(surface_tampon_totale=42, rayon_zone_tampon=2)
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    zone_infestee_1 = ZoneInfesteeFactory(
        fiche_zone_delimitee=fiche_zone_delimitee, surface_infestee_totale=17.5, rayon=3
    )
    fiche_detection_fiche_zone_delimitee = FicheDetectionFactory(hors_zone_infestee=fiche_zone_delimitee)
    fiche_detection_zone_infestee_1 = FicheDetectionFactory(zone_infestee=zone_infestee_1)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()

    expect(page.get_by_text(fiche_zone_delimitee.commentaire, exact=True)).to_be_visible()
    rayon_zone_tampon = str(fiche_zone_delimitee.rayon_zone_tampon).rstrip("0").rstrip(".")
    expect(
        page.get_by_text(f"{rayon_zone_tampon} {fiche_zone_delimitee.unite_rayon_zone_tampon}", exact=True)
    ).to_be_visible()
    surface_tampon_totale = str(fiche_zone_delimitee.surface_tampon_totale).rstrip("0").rstrip(".")
    expect(
        page.get_by_text(f"{surface_tampon_totale} {fiche_zone_delimitee.unite_surface_tampon_totale}", exact=True)
    ).to_be_visible()
    expect(page.get_by_role("link", name=f"{str(fiche_detection_fiche_zone_delimitee.numero)}")).to_be_visible()
    expect(page.get_by_text(f"{zone_infestee_1.nom}", exact=True)).to_be_visible()
    expect(page.get_by_text(f"{zone_infestee_1.get_caracteristique_principale_display()}", exact=True)).to_be_visible()
    expect(
        page.get_by_text(
            f"{str(zone_infestee_1.rayon).rstrip('0').rstrip('.')} {zone_infestee_1.unite_rayon}", exact=True
        )
    ).to_be_visible()
    expect(
        page.get_by_text(
            f"{str(zone_infestee_1.surface_infestee_totale).rstrip('0').rstrip('.')} {zone_infestee_1.unite_surface_infestee_totale}",
            exact=True,
        )
    ).to_be_visible()
    expect(page.get_by_role("link", name=f"{str(fiche_detection_zone_infestee_1.numero)}")).to_be_visible()

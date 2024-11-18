from playwright.sync_api import Page, expect
from model_bakery import baker

from core.models import Visibilite
from sv.models import ZoneInfestee, FicheDetection


def test_fichezonedelimitee_with_zoneinfestee_detail(live_server, fiche_zone, page: Page, mocked_authentification_user):
    fiche_zone_delimitee = fiche_zone
    zone_infestee_1 = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True)
    fiche_detection_fiche_zone_delimitee = baker.make(
        FicheDetection, hors_zone_infestee=fiche_zone_delimitee, visibilite=Visibilite.LOCAL
    )
    fiche_detection_zone_infestee_1 = baker.make(
        FicheDetection, zone_infestee=zone_infestee_1, visibilite=Visibilite.LOCAL
    )
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Fiche zone délimitée n° {fiche_zone_delimitee.numero}")).to_be_visible()
    expect(page.get_by_text(str(fiche_zone_delimitee.organisme_nuisible))).to_be_visible()
    expect(page.get_by_text(str(fiche_zone_delimitee.statut_reglementaire))).to_be_visible()
    expect(page.get_by_text(fiche_zone_delimitee.commentaire)).to_be_visible()
    expect(
        page.get_by_text(f"{fiche_zone_delimitee.rayon_zone_tampon} {fiche_zone_delimitee.unite_rayon_zone_tampon}")
    ).to_be_visible()
    expect(
        page.get_by_text(
            f"{fiche_zone_delimitee.surface_tampon_totale} {fiche_zone_delimitee.unite_surface_tampon_totale}"
        )
    ).to_be_visible()
    expect(page.get_by_text(f"{str(fiche_zone_delimitee.createur)}")).to_be_visible()
    expect(page.get_by_text(fiche_zone_delimitee.date_creation.strftime("%d/%m/%Y"))).to_be_visible()
    expect(page.get_by_role("link", name=f"{str(fiche_detection_fiche_zone_delimitee.numero)}")).to_be_visible()
    expect(page.get_by_text(f"{zone_infestee_1.nom}")).to_be_visible()
    expect(page.get_by_text(f"{zone_infestee_1.get_caracteristique_principale_display()}")).to_be_visible()
    expect(page.get_by_text(f"{zone_infestee_1.rayon} {zone_infestee_1.unite_rayon}")).to_be_visible()
    expect(
        page.get_by_text(f"{zone_infestee_1.surface_infestee_totale} {zone_infestee_1.unite_surface_infestee_totale}")
    ).to_be_visible()
    expect(page.get_by_role("link", name=f"{str(fiche_detection_zone_infestee_1.numero)}")).to_be_visible()

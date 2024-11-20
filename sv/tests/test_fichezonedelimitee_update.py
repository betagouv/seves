from playwright.sync_api import Page, expect
from model_bakery import baker

from core.models import LienLibre, Visibilite
from sv.tests.test_utils import FicheZoneDelimiteeFormPage
from sv.models import ZoneInfestee, FicheZoneDelimitee, FicheDetection, Etat


def test_fichezonedelimitee_update_form_content(
    live_server, page: Page, choice_js_fill, fiche_detection_bakery, fiche_zone_bakery
):
    fiche_zone_delimitee = fiche_zone_bakery()

    for _ in range(3):
        fiche_detection = fiche_detection_bakery()
        fiche_detection.organisme_nuisible = fiche_zone_delimitee.organisme_nuisible
        fiche_detection.statut_reglementaire = fiche_zone_delimitee.statut_reglementaire
        fiche_detection.hors_zone_infestee = fiche_zone_delimitee
        fiche_detection.save()

    zones_infestees = baker.make(
        ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True, _quantity=2
    )

    for zone_infestee in zones_infestees:
        for _ in range(2):
            fiche_detection = fiche_detection_bakery()
            fiche_detection.organisme_nuisible = fiche_zone_delimitee.organisme_nuisible
            fiche_detection.statut_reglementaire = fiche_zone_delimitee.statut_reglementaire
            fiche_detection.zone_infestee = zone_infestee
            fiche_detection.save()

    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.check_update_form_content(fiche_zone_delimitee)


def test_organisme_nuisible_and_statut_reglementaire_are_readonly_on_fiche_zone_delimitee_update_form(
    live_server, page: Page, fiche_zone_bakery, choice_js_fill
):
    fiche_zone_delimitee = fiche_zone_bakery()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.organisme_nuisible_is_readonly()
    form_page.statut_reglementaire_is_readonly()


def test_fichezonedelimitee_update_without_zone_infestee_form_submit(
    live_server, page: Page, fiche_zone_bakery, choice_js_fill
):
    fiche_zone_delimitee = fiche_zone_bakery()
    new_fiche_zone_delimitee = baker.prepare(
        FicheZoneDelimitee, _fill_optional=True, etat=Etat.objects.get(id=Etat.get_etat_initial())
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.fill_form(new_fiche_zone_delimitee)
    form_page.submit_update_form()
    fiche_zone_delimitee_updated = FicheZoneDelimitee.objects.get(id=fiche_zone_delimitee.id)
    assert fiche_zone_delimitee_updated.date_creation.replace(
        microsecond=0
    ) == fiche_zone_delimitee.date_creation.replace(microsecond=0)
    assert fiche_zone_delimitee_updated.numero == fiche_zone_delimitee.numero
    assert fiche_zone_delimitee_updated.createur == fiche_zone_delimitee.createur
    assert fiche_zone_delimitee_updated.organisme_nuisible == fiche_zone_delimitee.organisme_nuisible
    assert fiche_zone_delimitee_updated.statut_reglementaire == fiche_zone_delimitee.statut_reglementaire
    assert fiche_zone_delimitee_updated.commentaire == new_fiche_zone_delimitee.commentaire
    assert fiche_zone_delimitee_updated.rayon_zone_tampon == new_fiche_zone_delimitee.rayon_zone_tampon
    assert fiche_zone_delimitee_updated.unite_rayon_zone_tampon == new_fiche_zone_delimitee.unite_rayon_zone_tampon
    assert fiche_zone_delimitee_updated.surface_tampon_totale == new_fiche_zone_delimitee.surface_tampon_totale
    assert (
        fiche_zone_delimitee_updated.unite_surface_tampon_totale == new_fiche_zone_delimitee.unite_surface_tampon_totale
    )


def test_update_zone_infestee(live_server, page: Page, fiche_zone_bakery, choice_js_fill):
    fiche_zone_delimitee = fiche_zone_bakery()
    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True)
    new_zone_infestee = baker.prepare(ZoneInfestee, _fill_optional=True)
    fiche_detection = baker.make(
        FicheDetection,
        organisme_nuisible=fiche_zone_delimitee.organisme_nuisible,
        statut_reglementaire=fiche_zone_delimitee.statut_reglementaire,
        visibilite=Visibilite.LOCAL,
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.fill_zone_infestee_form(0, new_zone_infestee, (fiche_detection,))
    form_page.submit_update_form()
    zone_infestee_updated = ZoneInfestee.objects.get(id=zone_infestee.id)
    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert zone_infestee_updated.nom == new_zone_infestee.nom
    assert zone_infestee_updated.caracteristique_principale == new_zone_infestee.caracteristique_principale
    assert zone_infestee_updated.surface_infestee_totale == new_zone_infestee.surface_infestee_totale
    assert zone_infestee_updated.unite_surface_infestee_totale == new_zone_infestee.unite_surface_infestee_totale
    assert zone_infestee_updated.rayon == new_zone_infestee.rayon
    assert zone_infestee_updated.unite_rayon == new_zone_infestee.unite_rayon
    assert fiche_detection_updated.zone_infestee == zone_infestee_updated


def test_add_zone_infestee(live_server, page: Page, fiche_zone_bakery, choice_js_fill):
    fiche_zone_delimitee = fiche_zone_bakery()
    baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True)
    new_zone_infestee = baker.prepare(ZoneInfestee, _fill_optional=True)
    fiche_detection = baker.make(
        FicheDetection,
        organisme_nuisible=fiche_zone_delimitee.organisme_nuisible,
        statut_reglementaire=fiche_zone_delimitee.statut_reglementaire,
        visibilite=Visibilite.LOCAL,
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.add_new_zone_infestee(new_zone_infestee, (fiche_detection,))
    form_page.submit_update_form()
    zone_infestee_created = ZoneInfestee.objects.get(
        fiche_zone_delimitee=fiche_zone_delimitee, nom=new_zone_infestee.nom
    )
    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert zone_infestee_created.nom == new_zone_infestee.nom
    assert zone_infestee_created.caracteristique_principale == new_zone_infestee.caracteristique_principale
    assert zone_infestee_created.surface_infestee_totale == new_zone_infestee.surface_infestee_totale
    assert zone_infestee_created.unite_surface_infestee_totale == new_zone_infestee.unite_surface_infestee_totale
    assert zone_infestee_created.rayon == new_zone_infestee.rayon
    assert zone_infestee_created.unite_rayon == new_zone_infestee.unite_rayon
    assert fiche_detection_updated.zone_infestee == zone_infestee_created


def test_update_form_cant_have_same_detection_in_hors_zone_infestee_and_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
) -> None:
    fiche_zone_delimitee = baker.make(
        FicheZoneDelimitee,
        etat=Etat.objects.get(id=Etat.get_etat_initial()),
        organisme_nuisible=fiche_detection.organisme_nuisible,
        statut_reglementaire=fiche_detection.statut_reglementaire,
        _fill_optional=True,
    )
    baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.select_detections_in_zone_infestee(0, (fiche_detection,))
    form_page.submit_update_form()
    expect(
        page.get_by_text(
            f"La fiche détection {str(fiche_detection.numero)} ne peut pas être sélectionnée à la fois dans les zones infestées et dans hors zone infestée."
        )
    ).to_be_visible()
    fiche_detection.refresh_from_db()
    assert fiche_detection.zone_infestee is None


def test_update_form_cant_have_same_detection_in_two_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
) -> None:
    fiche_zone_delimitee = baker.make(
        FicheZoneDelimitee,
        etat=Etat.objects.get(id=Etat.get_etat_initial()),
        organisme_nuisible=fiche_detection.organisme_nuisible,
        statut_reglementaire=fiche_detection.statut_reglementaire,
        _fill_optional=True,
    )
    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True)
    fiche_detection.zone_infestee = zone_infestee
    fiche_detection.save()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.add_new_zone_infestee(baker.prepare(ZoneInfestee, _fill_optional=True), (fiche_detection,))
    form_page.submit_update_form()
    expect(
        page.get_by_text(
            f"Les fiches détection suivantes sont dupliquées dans les zones infestées : {str(fiche_detection.numero)}."
        )
    ).to_be_visible()


def test_update_fiche_can_add_and_delete_free_links(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    fiche_detection_bakery,
    choice_js_fill,
):
    other_fiche = fiche_detection_bakery()
    other_fiche_2 = fiche_detection_bakery()
    fiche_zone_delimitee = baker.make(
        FicheZoneDelimitee,
        etat=Etat.objects.get(id=Etat.get_etat_initial()),
        organisme_nuisible=fiche_detection.organisme_nuisible,
        statut_reglementaire=fiche_detection.statut_reglementaire,
        _fill_optional=True,
    )
    LienLibre.objects.create(related_object_1=fiche_zone_delimitee, related_object_2=other_fiche)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")

    expect(page.get_by_text(f"Fiche Détection : {str(other_fiche.numero)}Remove item")).to_be_visible()
    # Remove existing link
    page.locator(".choices__button").click()

    # Add new link
    fiche_input = "Fiche Détection : " + str(other_fiche_2.numero)
    choice_js_fill(page, "#liens-libre .choices", str(other_fiche_2.numero), fiche_input)

    form_page.submit_update_form()

    page.wait_for_timeout(600)

    assert LienLibre.objects.count() == 1
    lien_libre = LienLibre.objects.get()

    assert lien_libre.related_object_1 == fiche_zone_delimitee
    assert lien_libre.related_object_2 == other_fiche_2


def test_update_fiche_zone_cant_add_self_links(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    choice_js_fill,
):
    fiche_zone_delimitee = baker.make(
        FicheZoneDelimitee,
        etat=Etat.objects.get(id=Etat.get_etat_initial()),
        organisme_nuisible=fiche_detection.organisme_nuisible,
        statut_reglementaire=fiche_detection.statut_reglementaire,
        _fill_optional=True,
        visibilite=Visibilite.NATIONAL,
    )
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")

    fiche_input = "Fiche zone délimitée : " + str(fiche_zone_delimitee.numero)
    page.query_selector("#liens-libre .choices").click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill(fiche_input)
    expect(page.get_by_role("option", name=fiche_input, exact=True)).not_to_be_visible()

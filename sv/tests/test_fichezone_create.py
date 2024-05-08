import pytest
from playwright.sync_api import Page, expect
from model_bakery import baker
from django.utils import timezone
from django.db.utils import IntegrityError
from sv.models import FicheZoneDelimitee, ZoneInfestee, FicheDetection
from sv.tests.test_utils import FicheZoneDelimiteeFormPage


@pytest.mark.django_db
def test_can_create_fiche_zone_delimitee_without_zone_infestee(live_server, page: Page, choice_js_fill) -> None:
    fiche = baker.prepare(FicheZoneDelimitee, _fill_optional=True)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.navigate(live_server)
    form_page.fill_form(fiche)
    form_page.send_form()

    form_page.check_message_succes()
    assert FicheZoneDelimitee.objects.count() == 1
    assert ZoneInfestee.objects.count() == 0


@pytest.mark.django_db
def test_can_create_fiche_zone_delimitee_with_2_zones_infestees(live_server, page: Page, choice_js_fill) -> None:
    detections_hors_zone_infestee, detections_zone_infestee1, detections_zone_infestee2 = (
        baker.make(FicheDetection, _quantity=2) for _ in range(3)
    )
    fiche = baker.prepare(FicheZoneDelimitee, _fill_optional=True)
    zone_infestee1, zone_infestee2 = baker.prepare(
        ZoneInfestee, fiche_zone_delimitee=fiche, _fill_optional=True, _quantity=2
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.navigate(live_server)
    form_page.fill_form(fiche, zone_infestee1, detections_hors_zone_infestee, detections_zone_infestee1)
    form_page.add_new_zone_infestee(zone_infestee2, detections_zone_infestee2)
    form_page.send_form()

    form_page.check_message_succes()
    # Vérification des attributs de FicheZoneDelimitee
    assert FicheZoneDelimitee.objects.count() == 1
    fiche_from_db = FicheZoneDelimitee.objects.get()
    assert fiche_from_db.date_creation.date() == timezone.now().date()
    assert (
        fiche_from_db.caracteristiques_principales_zone_delimitee == fiche.caracteristiques_principales_zone_delimitee
    )
    assert fiche_from_db.vegetaux_infestes == fiche.vegetaux_infestes
    assert fiche_from_db.commentaire == fiche.commentaire
    assert fiche_from_db.rayon_zone_tampon == fiche.rayon_zone_tampon
    assert fiche_from_db.unite_rayon_zone_tampon == fiche.unite_rayon_zone_tampon
    assert fiche_from_db.surface_tampon_totale == fiche.surface_tampon_totale
    assert fiche_from_db.unite_surface_tampon_totale == fiche.unite_surface_tampon_totale
    assert fiche_from_db.is_zone_tampon_toute_commune == fiche.is_zone_tampon_toute_commune

    # Vérification des détections hors zone infestée
    assert all(detection in detections_hors_zone_infestee for detection in fiche_from_db.fichedetection_set.all())

    # Vérification des zones infestées
    zones_infestees_from_db = fiche_from_db.zoneinfestee_set.all()
    assert zones_infestees_from_db.count() == 2
    for zone_infestee, detections_zone_infestee, zone_infestee_from_db in zip(
        [zone_infestee1, zone_infestee2],
        [detections_zone_infestee1, detections_zone_infestee2],
        zones_infestees_from_db,
    ):
        assert zone_infestee_from_db.numero == zone_infestee.numero
        assert zone_infestee_from_db.surface_infestee_totale == zone_infestee.surface_infestee_totale
        assert zone_infestee_from_db.unite_surface_infestee_totale == zone_infestee.unite_surface_infestee_totale
        assert all(
            detection in detections_zone_infestee for detection in zone_infestee_from_db.fichedetection_set.all()
        )


# TODO
# test l'affichage d'un message d'erreur s'il manque le numéro de la zone infestée et la surface infestée totale
# dans le formulaire d'une zone infestée


def test_cant_have_same_detection_in_hors_zone_infestee_and_zone_infestee(
    live_server, page: Page, choice_js_fill
) -> None:
    fiche_zone_delimitee = baker.prepare(FicheZoneDelimitee, _fill_optional=True)
    zone_infestee = baker.prepare(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True)
    detection = baker.make(FicheDetection)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.navigate(live_server)
    form_page.fill_form(fiche_zone_delimitee, zone_infestee, (detection,), (detection,))
    form_page.send_form()

    # form_page.check_message_erreur()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


def test_cant_have_same_detection_in_zone_infestee_forms(live_server, page: Page, choice_js_fill) -> None:
    fiche_zone_delimitee = baker.prepare(FicheZoneDelimitee, _fill_optional=True)
    zone_infestee1, zone_infestee2 = baker.prepare(
        ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _fill_optional=True, _quantity=2
    )
    detection = baker.make(FicheDetection)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.navigate(live_server)
    form_page.fill_form(fiche_zone_delimitee, zone_infestee1, (), (detection,))
    form_page.add_new_zone_infestee(zone_infestee2, (detection,))
    form_page.send_form()

    expect(
        page.get_by_text(
            f"La fiche détection {str(detection.numero)} ne peut pas être sélectionnée à la fois dans les zones infestées et dans hors zone infestée."
        )
    ).to_be_visible()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


# Test des contraintes de base de données du modèle FicheDetection (hors_zone_infestee et zone_infestee)
@pytest.mark.django_db
def test_fiche_detection_with_no_zones():
    baker.make(FicheDetection, hors_zone_infestee=None, zone_infestee=None)
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_zone_infestee():
    baker.make(
        FicheDetection,
        hors_zone_infestee=None,
        zone_infestee=baker.make(ZoneInfestee, fiche_zone_delimitee=baker.make(FicheZoneDelimitee)),
    )
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_hors_zone_infestee():
    baker.make(
        FicheDetection,
        hors_zone_infestee=baker.make(FicheZoneDelimitee),
        zone_infestee=None,
    )
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_hors_zone_infestee_and_zone_infestee():
    with pytest.raises(IntegrityError):
        baker.make(
            FicheDetection,
            hors_zone_infestee=baker.make(FicheZoneDelimitee),
            zone_infestee=baker.make(ZoneInfestee, fiche_zone_delimitee=baker.make(FicheZoneDelimitee)),
        )

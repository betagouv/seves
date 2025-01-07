import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from playwright.sync_api import Page, expect

from sv.factories import FicheDetectionFactory, EvenementFactory
from sv.models import FicheZoneDelimitee, ZoneInfestee, FicheDetection
from sv.tests.test_utils import FicheZoneDelimiteeFormPage


@pytest.mark.django_db
def test_can_go_back_to_event_from_fiche_zone_form(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, evenement)
    form_page.page.get_by_role("link", name="Annuler").click()

    assert form_page.page.url == f"{live_server.url}{evenement.get_absolute_url()}"


@pytest.mark.django_db
def test_fiche_detection_are_filtered_by_evenement_of_fiche_detection(client):
    """Test que les fiches détection proposées dans la page de création de la fiche zone délimitée viennent du même événement"""
    fiche = FicheDetectionFactory()
    fiches_same_evenement = FicheDetectionFactory.create_batch(3, evenement=fiche.evenement)
    fiches_other_evenement = FicheDetectionFactory.create_batch(3)

    url = f"{reverse('fiche-zone-delimitee-creation')}?evenement={fiche.evenement.pk}"
    response = client.get(url)
    context = response.context
    form = context["form"]
    queryset = form.fields["detections_hors_zone"].queryset

    assert not any(fiche in queryset for fiche in fiches_other_evenement)
    assert all(fiche in queryset for fiche in fiches_same_evenement)


@pytest.mark.django_db
def test_can_create_fiche_zone_delimitee_without_zone_infestee(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    fiche = baker.prepare(
        FicheZoneDelimitee,
        _fill_optional=True,
        rayon_zone_tampon=10,
        surface_tampon_totale=15,
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, evenement)
    form_page.fill_form(fiche)
    form_page.save()

    form_page.check_message_succes()
    assert ZoneInfestee.objects.count() == 0
    assert FicheZoneDelimitee.objects.count() == 1
    fiche_from_db = FicheZoneDelimitee.objects.get()
    assert fiche_from_db.date_creation.date() == timezone.now().date()
    assert fiche_from_db.commentaire == fiche.commentaire
    assert fiche_from_db.rayon_zone_tampon == fiche.rayon_zone_tampon
    assert fiche_from_db.unite_rayon_zone_tampon == fiche.unite_rayon_zone_tampon
    assert fiche_from_db.surface_tampon_totale == fiche.surface_tampon_totale
    assert fiche_from_db.unite_surface_tampon_totale == fiche.unite_surface_tampon_totale


@pytest.mark.django_db
def test_can_create_fiche_zone_delimitee_with_2_zones_infestees(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    evenement = EvenementFactory()
    detections_hors_zone_infestee, detections_zone_infestee1, detections_zone_infestee2 = (
        baker.make(
            FicheDetection,
            evenement=evenement,
            _quantity=2,
        )
        for _ in range(3)
    )
    fiche = baker.prepare(
        FicheZoneDelimitee,
        _fill_optional=True,
        rayon_zone_tampon=10,
        surface_tampon_totale=15,
    )
    zone_infestee1, zone_infestee2 = baker.prepare(
        ZoneInfestee, fiche_zone_delimitee=fiche, _fill_optional=True, _quantity=2, surface_infestee_totale=10, rayon=15
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, evenement)
    form_page.fill_form(fiche, zone_infestee1, detections_hors_zone_infestee, detections_zone_infestee1)
    form_page.add_new_zone_infestee(zone_infestee2, detections_zone_infestee2)
    form_page.save()

    form_page.check_message_succes()
    # Vérification des attributs de FicheZoneDelimitee
    assert FicheZoneDelimitee.objects.count() == 1
    fiche_from_db = FicheZoneDelimitee.objects.get()
    assert fiche_from_db.date_creation.date() == timezone.now().date()
    assert fiche_from_db.commentaire == fiche.commentaire
    assert fiche_from_db.rayon_zone_tampon == fiche.rayon_zone_tampon
    assert fiche_from_db.unite_rayon_zone_tampon == fiche.unite_rayon_zone_tampon
    assert fiche_from_db.surface_tampon_totale == fiche.surface_tampon_totale
    assert fiche_from_db.unite_surface_tampon_totale == fiche.unite_surface_tampon_totale

    # Vérification des détections hors zone infestée
    detections_hors_zone_infestee.append(fiche_detection)
    assert all(detection in detections_hors_zone_infestee for detection in fiche_from_db.fichedetection_set.all())

    # Vérification des zones infestées
    zones_infestees_from_db = fiche_from_db.zoneinfestee_set.all()
    assert zones_infestees_from_db.count() == 2
    for zone_infestee, detections_zone_infestee, zone_infestee_from_db in zip(
        [zone_infestee1, zone_infestee2],
        [detections_zone_infestee1, detections_zone_infestee2],
        zones_infestees_from_db,
    ):
        assert zone_infestee_from_db.nom == zone_infestee.nom
        assert zone_infestee_from_db.caracteristique_principale == zone_infestee.caracteristique_principale
        assert zone_infestee_from_db.surface_infestee_totale == zone_infestee.surface_infestee_totale
        assert zone_infestee_from_db.unite_surface_infestee_totale == zone_infestee.unite_surface_infestee_totale
        assert all(
            detection in detections_zone_infestee for detection in zone_infestee_from_db.fichedetection_set.all()
        )


@pytest.mark.skip(reason="refacto evenement")
def test_cant_have_same_detection_in_hors_zone_infestee_and_zone_infestee(
    live_server, page: Page, choice_js_fill
) -> None:
    evenement = EvenementFactory()
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    fiche_zone_delimitee = baker.prepare(FicheZoneDelimitee)
    zone_infestee = baker.prepare(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, evenement)
    form_page.fill_form(fiche_zone_delimitee, zone_infestee, (), (fiche_detection,))
    form_page.save()

    expect(
        page.get_by_text(
            f"La fiche détection {str(fiche_detection.numero)} ne peut pas être sélectionnée à la fois dans les zones infestées et dans hors zone infestée."
        )
    ).to_be_visible()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


def test_cant_have_same_detection_in_zone_infestee_forms(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    fiche_zone_delimitee = baker.prepare(FicheZoneDelimitee)
    zone_infestee1, zone_infestee2 = baker.prepare(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _quantity=2)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, evenement)
    form_page.fill_form(fiche_zone_delimitee, zone_infestee1, (), (fiche_detection,))
    form_page.add_new_zone_infestee(zone_infestee2, (fiche_detection,))
    form_page.save()

    expect(page.get_by_text("Erreurs dans le(s) formulaire(s) Zones infestées")).to_be_visible()
    expect(
        page.get_by_text(
            f"Les fiches détection suivantes sont dupliquées dans les zones infestées : {str(fiche_detection.numero)}."
        )
    ).to_be_visible()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


@pytest.mark.django_db
def test_cant_access_create_fiche_zone_delimitee_form_when_evenement_is_already_linked(
    live_server, page: Page, choice_js_fill
):
    """Test que l'accès direct au formulaire de création (via l'URL) d'une fiche zone délimitée avec un événement déjà rattaché affiche un message d'erreur"""
    fiche_zone_delimitee = baker.make(FicheZoneDelimitee)
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, evenement)
    expect(page.get_by_text("L'événement est déjà rattaché à une fiche zone délimitée")).to_be_visible()


def test_cant_fill_negative_value_for_surface_and_rayon(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, evenement)
    assert form_page.rayon_zone_tampon.get_attribute("min") == "0"
    assert form_page.surface_tampon_totale.get_attribute("min") == "0"
    assert (
        form_page.page.locator(form_page.zone_infestee_surface_infestee_totale_base_locator.format(0)).get_attribute(
            "min"
        )
        == "0"
    )
    assert (
        form_page.page.locator(form_page.zone_infestee_surface_infestee_totale_base_locator.format(0)).get_attribute(
            "min"
        )
        == "0"
    )


def test_has_same_surface_units_order_for_zone_tampon_and_zone_infestee(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, evenement)
    assert form_page.has_same_surface_units_order_for_zone_tampon_and_zone_infestee() is True


def test_has_same_rayon_units_order_for_zone_tampon_and_zone_infestee(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, evenement)
    assert form_page.has_same_rayon_units_order_for_zone_tampon_and_zone_infestee() is True

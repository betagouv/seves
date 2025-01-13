from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect, Page

from core.models import Visibilite, Structure
from sv.factories import EvenementFactory, FicheZoneFactory, FicheDetectionFactory
from sv.models import Evenement, FicheDetection


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


def test_can_delete_evenement(live_server, page):
    evenement = EvenementFactory()
    assert Evenement.objects.count() == 1
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    page.get_by_text("Supprimer l'événement", exact=True).click()
    page.get_by_test_id("submit-evenement-delete").click()

    expect(page.get_by_text("Objet supprimé avec succès")).to_be_visible()

    assert Evenement.objects.count() == 0
    assert Evenement._base_manager.get().pk == evenement.pk


def test_cant_forge_deletion_of_evenement_we_cant_see(client, mocked_authentification_user):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("soft-delete"), data=payload)

    assert response.status_code == 302
    evenement.refresh_from_db()
    assert evenement.is_deleted is False


def test_delete_evenement_will_delete_associated_detections(live_server, page):
    evenement = EvenementFactory()
    FicheDetectionFactory.create_batch(3, evenement=evenement)
    fiche_detection = FicheDetectionFactory()
    assert Evenement.objects.count() == 2
    assert FicheDetection.objects.count() == 4
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    page.get_by_text("Supprimer l'événement", exact=True).click()
    page.get_by_test_id("submit-evenement-delete").click()

    expect(page.get_by_text("Objet supprimé avec succès")).to_be_visible()

    evenement_not_deleted = Evenement.objects.get()
    assert evenement_not_deleted == fiche_detection.evenement
    assert Evenement._base_manager.filter(is_deleted=True).get().pk == evenement.pk

    fiche_not_deleted = FicheDetection.objects.get()
    assert fiche_not_deleted == fiche_detection
    assert FicheDetection._base_manager.filter(evenement=evenement).count() == 3


def test_evenement_can_view_basic_data(live_server, page: Page):
    evenement = EvenementFactory()
    FicheDetectionFactory(evenement=evenement)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    expect(page.get_by_text(evenement.organisme_nuisible.libelle_court)).to_be_visible()
    expect(page.get_by_text(evenement.organisme_nuisible.code_oepp)).to_be_visible()
    expect(page.get_by_text(evenement.statut_reglementaire.libelle)).to_be_visible()
    expect(page.get_by_text("Dernière mise à jour le ")).to_be_visible()

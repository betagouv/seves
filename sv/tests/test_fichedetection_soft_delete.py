import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from playwright.sync_api import expect

from core.models import Structure
from sv.factories import FicheDetectionFactory
from sv.models import FicheDetection


@pytest.mark.django_db
def test_can_delete_fiche_detection(live_server, page):
    fiche_detection = FicheDetectionFactory()
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")

    page.get_by_text("Supprimer la détection", exact=True).click()
    page.get_by_test_id("submit-delete").click()

    expect(page.get_by_text("Objet supprimé avec succès")).to_be_visible()

    assert FicheDetection.objects.count() == 0
    expect(page.get_by_role("link", name=str(fiche_detection.numero))).not_to_be_visible()


@pytest.mark.django_db
def test_cant_forge_deletion_of_fiche_we_cant_see(client, mocked_authentification_user):
    fiche_detection = FicheDetectionFactory(evenement__createur=Structure.objects.create(libelle="A new structure"))
    response = client.get(fiche_detection.get_absolute_url())

    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(fiche_detection).id,
        "content_id": fiche_detection.pk,
    }
    response = client.post(reverse("soft-delete"), data=payload)

    assert response.status_code == 302
    fiche_detection.refresh_from_db()
    assert fiche_detection.is_deleted is False

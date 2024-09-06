import pytest

from playwright.sync_api import expect

from sv.models import FicheDetection


@pytest.mark.django_db
def test_can_delete_fiche_detection(live_server, page, fiche_detection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    page.get_by_test_id("fiche-action").click()
    page.get_by_role("link", name="Supprimer la fiche").click()
    page.get_by_test_id("submit-delete").click()

    expect(page.get_by_text("Objet supprimé avec succès")).to_be_visible()

    assert FicheDetection.objects.count() == 0
    expect(page.get_by_role("link", name=str(fiche_detection.numero))).not_to_be_visible()

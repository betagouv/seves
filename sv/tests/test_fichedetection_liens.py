import pytest
from django.contrib.contenttypes.models import ContentType

from core.models import LienLibre
from playwright.sync_api import expect


@pytest.mark.django_db
def test_can_add_free_link(live_server, page, fiche_detection, fiche_detection_bakery):
    other_fiche = fiche_detection_bakery()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    page.get_by_test_id("fiche-action").click()
    page.get_by_role("link", name="Ajouter un lien libre").click()
    page.locator("#id_object_choice").select_option(label=f"FicheDetection: {str(other_fiche.numero)}")
    page.get_by_test_id("submit-freelink").click()

    expect(page.get_by_text("Le lien a été créé avec succès.")).to_be_visible()

    link = LienLibre.objects.get()
    assert link.content_type_1 == ContentType.objects.get_for_model(other_fiche)
    assert link.content_type_2 == ContentType.objects.get_for_model(other_fiche)
    assert link.object_id_1 == fiche_detection.pk
    assert link.object_id_2 == other_fiche.pk

    expect(page.get_by_role("link", name=str(other_fiche.numero))).to_be_visible()


@pytest.mark.django_db
def test_cant_link_to_self(live_server, page, fiche_detection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    page.get_by_test_id("fiche-action").click()
    page.get_by_role("link", name="Ajouter un lien libre").click()
    page.wait_for_selector("#id_object_choice")
    page.locator("#id_object_choice").select_option(label=f"FicheDetection: {str(fiche_detection.numero)}")
    page.get_by_test_id("submit-freelink").click()

    expect(page.get_by_text("Vous ne pouvez pas lier un objet à lui même.")).to_be_visible()

    assert LienLibre.objects.count() == 0


@pytest.mark.django_db
def test_cant_link_if_links_exists(live_server, page, fiche_detection, fiche_detection_bakery):
    other_fiche = fiche_detection_bakery()
    content_type = ContentType.objects.get_for_model(other_fiche)
    LienLibre.objects.create(
        object_id_1=fiche_detection.pk,
        content_type_1=content_type,
        object_id_2=other_fiche.pk,
        content_type_2=content_type,
    )

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    page.get_by_test_id("fiche-action").click()
    page.get_by_role("link", name="Ajouter un lien libre").click()
    page.wait_for_selector("#id_object_choice")
    page.locator("#id_object_choice").select_option(label=f"FicheDetection: {str(other_fiche.numero)}")
    page.get_by_test_id("submit-freelink").click()

    expect(page.get_by_text("Ce lien existe déjà.")).to_be_visible()

    assert LienLibre.objects.count() == 1

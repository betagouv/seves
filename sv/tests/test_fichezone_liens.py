import pytest
from django.contrib.contenttypes.models import ContentType

from core.models import LienLibre
from playwright.sync_api import expect


@pytest.mark.django_db
def test_can_add_free_link(live_server, page, fiche_zone_bakery, choice_js_fill):
    fiche = fiche_zone_bakery()
    other_fiche = fiche_zone_bakery()
    page.goto(f"{live_server.url}{fiche.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Ajouter un lien libre").click()
    page.wait_for_selector("#fr-modal-freelink .choices__list--single")
    choice_js_fill(
        page,
        "#fr-modal-freelink .choices__list--single",
        f"Fiche Zone Delimitee: {str(other_fiche.numero)}",
        f"Fiche Zone Delimitee: {str(other_fiche.numero)}",
    )
    page.get_by_test_id("submit-freelink").click()

    expect(page.get_by_text("Le lien a été créé avec succès.")).to_be_visible()

    link = LienLibre.objects.get()
    assert link.content_type_1 == ContentType.objects.get_for_model(other_fiche)
    assert link.content_type_2 == ContentType.objects.get_for_model(other_fiche)
    assert link.object_id_1 == fiche.pk
    assert link.object_id_2 == other_fiche.pk

    expect(page.get_by_role("link", name=str(other_fiche.numero))).to_be_visible()

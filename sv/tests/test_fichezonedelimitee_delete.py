from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest

from core.factories import StructureFactory
from sv.factories import EvenementFactory, FicheZoneFactory
from sv.models import Evenement, FicheZoneDelimitee


@pytest.mark.django_db
def test_can_delete_fichezonedelimitee(live_server, page: Page):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()
    page.get_by_role("button", name="Supprimer la zone").click()
    page.get_by_role("button", name="Supprimer", exact=True).click()

    expect(page.get_by_role("heading", name="La zone a bien été supprimée")).to_be_visible()
    assert FicheZoneDelimitee.objects.filter(evenement=evenement).count() == 0


@pytest.mark.django_db
def test_cant_delete_fiche_zone_delimitee_without_permission(client, mocked_authentification_user):
    fiche_zone = FicheZoneFactory(createur=StructureFactory())
    evenement = EvenementFactory(
        createur=StructureFactory(), fiche_zone_delimitee=fiche_zone, etat=Evenement.Etat.BROUILLON
    )

    response = client.get(fiche_zone.get_absolute_url())
    assert response.status_code == 403
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    response = client.post(reverse("sv:fiche-zone-delimitee-delete", kwargs={"pk": fiche_zone.pk}), data={"next": "/"})
    assert response.status_code == 403

    fiche_zone.refresh_from_db()
    assert FicheZoneDelimitee.objects.filter(pk=fiche_zone.pk).exists()


def test_cant_see_delete_fiche_zone_delimitee_if_evenement_is_cloture(live_server, page: Page):
    evenement = EvenementFactory(fiche_zone_delimitee=FicheZoneFactory(), etat=Evenement.Etat.CLOTURE)

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()

    expect(page.get_by_role("button", name="Supprimer la zone")).not_to_be_visible()


@pytest.mark.django_db
def test_cant_delete_fiche_zone_delimitee_if_evenement_is_cloture(client, mocked_authentification_user):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone, etat=Evenement.Etat.CLOTURE)

    response = client.post(
        reverse("sv:fiche-zone-delimitee-delete", kwargs={"pk": fiche_zone.pk}),
        data={"next": evenement.get_absolute_url()},
    )
    assert response.status_code == 403

    fiche_zone.refresh_from_db()
    assert FicheZoneDelimitee.objects.filter(pk=fiche_zone.pk).exists()

from django.urls import reverse
from playwright.sync_api import Page, expect

from core.mixins import WithEtatMixin
from core.tests.generic_tests.actions import generic_test_ac_can_update_fiche_even_when_state_is_cloture
from sa.tests.factories import EvenementAnimalFactory


def test_can_update_evenement_animal(live_server, page: Page):
    evenement = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Modifier l'événement").click()
    page.locator("#id_commentaire").fill("Nouveau commentaire")
    page.get_by_role("button", name="Enregistrer").first.click()

    expect(page.get_by_text("L’évènement a bien été modifié.")).to_be_visible()
    expect(page.get_by_text(f"Événement {evenement.numero}", exact=True)).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.commentaire == "Nouveau commentaire"


def test_ac_can_update_evenement_animal_cloture(live_server, page: Page, mocked_authentification_user):
    generic_test_ac_can_update_fiche_even_when_state_is_cloture(
        live_server, page, EvenementAnimalFactory(), mocked_authentification_user, "#id_commentaire"
    )


def test_cant_update_evenement_animal_cloture_if_not_ac(client):
    evenement = EvenementAnimalFactory(etat=WithEtatMixin.Etat.CLOTURE)

    response = client.get(reverse("sa:evenement-animal-update", kwargs={"pk": evenement.pk}))
    assert response.status_code == 403

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from tiac.factories import EvenementSimpleFactory
from tiac.tests.pages import EvenementSimpleEditFormPage


@pytest.mark.django_db
def test_update_evenement_simple_performances(client, django_assert_num_queries):
    evenement = EvenementSimpleFactory()

    with django_assert_num_queries(14):
        client.get(reverse("tiac:evenement-simple-edition", kwargs={"pk": evenement.pk}))


def test_evenement_simple_update_has_locking_protection(
    live_server,
    page,
    mocked_authentification_user,
):
    evenement = EvenementSimpleFactory(contenu="AAA")
    update_page = EvenementSimpleEditFormPage(page, live_server.url, evenement)
    update_page.navigate()
    update_page.contenu.fill("BBB")

    evenement.contenu = "CCC"
    evenement.save()

    update_page.publish()
    update_page.page.wait_for_url("**edition**")

    evenement.refresh_from_db()
    assert evenement.contenu == "CCC"
    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    expect(
        page.get_by_text(
            "Vos modifications n'ont pas été enregistrées. Un autre utilisateur a modifié cet objet. Fermer cette modale pour charger la dernière version."
        )
    ).to_be_visible()
    page.keyboard.press("Escape")
    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")

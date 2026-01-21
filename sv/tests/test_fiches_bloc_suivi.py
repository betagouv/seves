import pytest
from playwright.sync_api import expect

from core.models import Visibilite
from sv.factories import EvenementFactory
from sv.models import Evenement


def test_evenement_does_not_have_bloc_suivi_display(live_server, page, mocked_authentification_user):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_label("Fil de suivi")).not_to_be_visible()
    expect(page.get_by_label("Contacts")).not_to_be_visible()
    expect(page.get_by_label("Documents")).not_to_be_visible()


@pytest.mark.parametrize(
    "visibilite",
    [
        Visibilite.LOCALE,
        Visibilite.NATIONALE,
    ],
)
def test_fiche_locale_or_nationale_have_bloc_suivi_display(
    live_server, page, visibilite: Visibilite, mocked_authentification_user
):
    evenement = EvenementFactory(visibilite=visibilite)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_label("Fil de suivi")).to_be_visible()
    expect(page.get_by_label("Contacts")).to_have_count(1)
    expect(page.get_by_label("Contacts")).to_be_hidden()
    expect(page.get_by_label("Documents", exact=True)).to_have_count(1)
    expect(page.get_by_label("Documents", exact=True)).to_be_hidden()

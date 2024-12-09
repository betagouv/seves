import pytest
from model_bakery import baker
from playwright.sync_api import expect

from core.models import Visibilite
from sv.models import FicheDetection, FicheZoneDelimitee


@pytest.mark.parametrize(
    "model_class",
    [
        FicheDetection,
        FicheZoneDelimitee,
    ],
)
def test_fiche_brouillon_does_not_have_bloc_suivi_display(live_server, page, mocked_authentification_user, model_class):
    fiche_detection = baker.make(
        model_class, visibilite=Visibilite.BROUILLON, createur=mocked_authentification_user.agent.structure
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_label("Fil de suivi")).not_to_be_visible()
    expect(page.get_by_label("Contacts")).not_to_be_visible()
    expect(page.get_by_label("Documents")).not_to_be_visible()


@pytest.mark.parametrize(
    "model_class,visibilite",
    [
        (FicheDetection, Visibilite.LOCAL),
        (FicheDetection, Visibilite.NATIONAL),
        (FicheZoneDelimitee, Visibilite.LOCAL),
        (FicheZoneDelimitee, Visibilite.NATIONAL),
    ],
)
def test_fiche_local_or_national_have_bloc_suivi_display(
    live_server, page, model_class, visibilite: Visibilite, mocked_authentification_user
):
    fiche_detection = baker.make(
        model_class, visibilite=visibilite, createur=mocked_authentification_user.agent.structure
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_label("Fil de suivi")).to_be_visible()
    expect(page.get_by_label("Contacts")).to_have_count(1)
    expect(page.get_by_label("Contacts")).to_be_hidden()
    expect(page.get_by_label("Documents")).to_have_count(1)
    expect(page.get_by_label("Documents")).to_be_hidden()

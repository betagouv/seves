import pytest
from playwright.sync_api import Page, expect
from django.urls import reverse

from core.factories import StructureFactory
from sv.factories import EvenementFactory, FicheDetectionFactory
from core.models import Structure, Visibilite
from core.constants import BSV_STRUCTURE, MUS_STRUCTURE, AC_STRUCTURE


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.BROUILLON, Visibilite.LOCAL, Visibilite.NATIONAL])
def test_agent_in_structure_createur_can_view_evenement(
    live_server, page: Page, mocked_authentification_user, visibilite_libelle: str
):
    fiche_detection = FicheDetectionFactory(evenement__visibilite=visibilite_libelle)
    response = page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    assert response.status == 200
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")

    if visibilite_libelle == Visibilite.BROUILLON:
        expect(page.get_by_text(str(fiche_detection.numero), exact=True)).to_be_visible()
        expect(page.get_by_text("non attribué", exact=True)).to_be_visible()
    else:
        expect(page.get_by_text(str(fiche_detection.evenement.numero), exact=True)).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.BROUILLON, Visibilite.LOCAL])
def test_agent_not_in_structure_createur_cannot_view_evenement_brouillon_or_local(
    live_server, page: Page, mocked_authentification_user, visibilite_libelle: str
):
    evenement = EvenementFactory(visibilite=visibilite_libelle)
    mocked_authentification_user.agent.structure = StructureFactory()
    mocked_authentification_user.agent.save()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("403 Forbidden")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name=str(evenement.numero))).not_to_be_visible()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_can_view_evenement_national(
    live_server, page: Page, mocked_authentification_user
):
    evenement = EvenementFactory(visibilite=Visibilite.NATIONAL)
    FicheDetectionFactory(evenement=evenement)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Événement {str(evenement.numero)}")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name=str(evenement.numero))).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_cannot_view_evenement_brouillon(
    live_server, page: Page, mocked_authentification_user, structure_ac: str
):
    evenement = EvenementFactory(visibilite=Visibilite.BROUILLON)
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("403 Forbidden")).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCAL, Visibilite.NATIONAL])
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_view_evenement(
    live_server,
    page: Page,
    mocked_authentification_user,
    visibilite_libelle: str,
    structure_ac: str,
):
    evenement = EvenementFactory(visibilite=visibilite_libelle)
    FicheDetectionFactory(evenement=evenement)
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert response.status == 200
    expect(page.get_by_role("heading", name=f"Événement {str(evenement.numero)}")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    page.wait_for_timeout(4000)
    expect(page.get_by_role("link", name=str(evenement.numero))).to_be_visible()

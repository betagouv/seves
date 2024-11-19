import pytest
from model_bakery import baker
from playwright.sync_api import Page, expect
from django.urls import reverse

from sv.models import FicheDetection
from core.models import Structure, Visibilite
from core.constants import BSV_STRUCTURE, MUS_STRUCTURE, AC_STRUCTURE

"""
Les tests vérifient :
- l'accès à une fiche de détection en fonction de sa visibilité et de l'agent connecté
- l'accès à la liste de fiches détection en fonction de la visibilité des fiches et de l'agent connecté
"""


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.BROUILLON, Visibilite.LOCAL, Visibilite.NATIONAL])
def test_agent_in_structure_createur_can_view_fiche_detection(
    live_server, page: Page, mocked_authentification_user, visibilite_libelle: str
):
    """Test qu'un agent appartennant à la structure créatrice d'une fiche de détection peut voir la fiche quelque soit sa visibilité"""
    fiche_detection = baker.make(
        FicheDetection, visibilite=visibilite_libelle, createur=mocked_authentification_user.agent.structure
    )
    response = page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    assert response.status == 200
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name=str(fiche_detection.createur))).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.BROUILLON, Visibilite.LOCAL])
def test_agent_not_in_structure_createur_cannot_view_fiche_detection_brouillon_or_local(
    live_server, page: Page, mocked_authentification_user, visibilite_libelle: str
):
    """Test qu'un agent n'appartenant pas à la structure créatrice d'une fiche détection ne peut pas voir la fiche
    si elle est en visibilité brouillon ou local"""
    fiche_detection = baker.make(FicheDetection, visibilite=visibilite_libelle)
    mocked_authentification_user.agent.structure = baker.make(Structure)
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_text("403 Forbidden")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name=str(fiche_detection.numero))).not_to_be_visible()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_can_view_fiche_detection_nationale(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user
):
    """Test qu'un agent n'appartenant pas à la structure créatrice d'une fiche détection peut voir la fiche
    si elle est en visibilité national"""
    fiche_detection.visibilite = Visibilite.NATIONAL
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Fiche détection n° {str(fiche_detection.numero)}")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name=str(fiche_detection.numero))).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_cannot_view_fiche_detection_brouillon(
    live_server, page: Page, mocked_authentification_user, structure_ac: str
):
    """Test qu'un agent appartenant à l'AC ne peut pas voir une fiche détection en visibilité brouillon"""
    fiche_detection = baker.make(FicheDetection, visibilite=Visibilite.BROUILLON)
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_text("403 Forbidden")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name=str(fiche_detection.numero))).not_to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCAL, Visibilite.NATIONAL])
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_view_fiche_detection(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    mocked_authentification_user,
    visibilite_libelle: str,
    structure_ac: str,
):
    """Test qu'un agent appartenant à l'AC peut voir une fiche détection en visibilité local ou national"""
    fiche_detection.visibilite = visibilite_libelle
    fiche_detection.save()
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Fiche détection n° {str(fiche_detection.numero)}")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    expect(page.get_by_role("link", name=str(fiche_detection.numero))).to_be_visible()

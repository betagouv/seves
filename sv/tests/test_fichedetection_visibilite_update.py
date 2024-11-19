import pytest
from model_bakery import baker
from playwright.sync_api import Page, expect
from django.urls import reverse

from sv.tests.test_utils import FicheDetectionFormDomElements
from sv.models import FicheDetection
from core.models import Structure, Visibilite
from core.constants import BSV_STRUCTURE, MUS_STRUCTURE, AC_STRUCTURE

"""
Les tests vérifient la modification de la visibilité d'une fiche de détection en de sa visibilité et de l'agent connecté
"""


def test_fiche_detection_visibilite_brouillon(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que l'enregistrement d'une fiche détection via le bouton "Enregistrer le brouillon" crée une visibilité brouillon"""
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    page.get_by_role("button", name="Enregistrer le brouillon").click()
    expect(page.get_by_text("brouillon")).to_be_visible()
    page.wait_for_timeout(600)
    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.visibilite == Visibilite.BROUILLON


def test_fiche_detection_visibilite_local(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que l'enregistrement d'une fiche détection via le bouton "Publier" crée une visibilité local"""
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    page.get_by_role("button", name="Publier").click()
    expect(page.get_by_text("local")).to_be_visible()
    page.wait_for_timeout(600)
    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.visibilite == Visibilite.LOCAL


@pytest.mark.django_db
def test_cannot_update_fiche_detection_visibilite_by_other_structures(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user
):
    """Test que les agents n'appartenant pas à la structure créatrice d'une fiche de détection ne peuvent pas modifier la visibilité de cette fiche
    lorsqu'elle est en visibilité national."""
    fiche_detection.visibilite = Visibilite.NATIONAL
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_text("Modifier la visibilité")).not_to_be_visible()


def test_agent_in_structure_createur_can_update_fiche_detection_visibilite_brouillon(
    live_server, page: Page, mocked_authentification_user
):
    """Test qu'un agent appartenant à la structure créatrice d'une fiche détection
    peut modifier la visibilité de cette fiche (passer en local) si elle est en visibilité brouillon"""
    fiche_detection = baker.make(
        FicheDetection, visibilite=Visibilite.BROUILLON, createur=mocked_authentification_user.agent.structure
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("link", name="Modifier la visibilité")).to_be_visible()
    page.get_by_role("link", name="Modifier la visibilité").click()
    page.get_by_text("Local").click()
    page.get_by_role("button", name="Valider").click()
    expect(page.get_by_role("heading", name="La visibilité de la fiche détection a bien été modifiée")).to_be_visible()
    expect(page.get_by_text(Visibilite.LOCAL)).to_be_visible()
    fiche_detection.refresh_from_db()
    assert fiche_detection.visibilite == Visibilite.LOCAL


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCAL, Visibilite.NATIONAL])
def test_agent_in_structure_createur_cannot_update_fiche_detection_visibilite(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user, visibilite_libelle: str
):
    """Test qu'un agent appartenant à la structure créatrice d'une fiche détection
    ne peut pas modifier la visibilité de cette fiche si elle est en visibilité local ou national"""
    fiche_detection.visibilite = visibilite_libelle
    fiche_detection.save()
    fiche_detection.createur = mocked_authentification_user.agent.structure
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_text("Modifier la visibilité")).not_to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_update_fiche_detection_visibilite_local_to_national(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user, structure_ac: str
):
    """Test qu'un agent appartenant à l'AC peut modifier la visibilité d'une fiche détection de local à national"""
    fiche_detection.visibilite = Visibilite.LOCAL
    fiche_detection.save()
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("link", name="Modifier la visibilité")).to_be_visible()
    page.get_by_role("link", name="Modifier la visibilité").click()
    page.get_by_text("National").click()
    page.get_by_role("button", name="Valider").click()
    expect(page.get_by_role("heading", name="La visibilité de la fiche détection a bien été modifiée")).to_be_visible()
    expect(page.get_by_text(Visibilite.NATIONAL, exact=True)).to_be_visible()
    fiche_detection.refresh_from_db()
    assert fiche_detection.visibilite == Visibilite.NATIONAL


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_update_fiche_detection_visibilite_national_to_local(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user, structure_ac: str
):
    """Test qu'un agent appartenant à l'AC peut modifier la visibilité d'une fiche détection de national à local"""
    fiche_detection.visibilite = Visibilite.NATIONAL
    fiche_detection.save()
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("link", name="Modifier la visibilité")).to_be_visible()
    page.get_by_role("link", name="Modifier la visibilité").click()
    page.get_by_text("Local").click()
    page.get_by_role("button", name="Valider").click()
    expect(page.get_by_role("heading", name="La visibilité de la fiche détection a bien été modifiée")).to_be_visible()
    expect(page.get_by_text(Visibilite.LOCAL, exact=True)).to_be_visible()
    fiche_detection.refresh_from_db()
    assert fiche_detection.visibilite == Visibilite.LOCAL


def test_publier_fiche_detection_from_btn(live_server, page: Page, mocked_authentification_user):
    fiche_detection = FicheDetection.objects.create(
        visibilite=Visibilite.BROUILLON, createur=mocked_authentification_user.agent.structure
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Publier").click()
    expect(page.get_by_role("heading", name="La visibilité de la fiche détection a bien été modifiée")).to_be_visible()
    expect(page.get_by_text(Visibilite.LOCAL)).to_be_visible()
    fiche_detection.refresh_from_db()
    assert fiche_detection.visibilite == Visibilite.LOCAL

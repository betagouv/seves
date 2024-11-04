import pytest
from playwright.sync_api import Page, expect
from core.models import Structure, Visibilite
from core.constants import BSV_STRUCTURE, MUS_STRUCTURE, AC_STRUCTURE


def _update_visibilite_fiche(fiche, visibilite_libelle):
    fiche.visibilite = visibilite_libelle
    fiche.save()


@pytest.mark.django_db
def test_cannot_update_fiche_zone_delimitee_visibilite_by_other_structures(
    live_server, page: Page, fiche_zone, mocked_authentification_user
):
    """Test que les agents n'appartenant pas à la structure créatrice d'une fiche ne peuvent pas modifier la visibilité de cette fiche
    lorsqu'elle est en visibilité national."""
    _update_visibilite_fiche(fiche_zone, Visibilite.NATIONAL)
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    expect(page.get_by_text("Modifier la visibilité")).not_to_be_visible()


def test_agent_in_structure_createur_can_update_fiche_zone_delimitee_visibilite_brouillon(
    live_server, page: Page, fiche_zone, mocked_authentification_user
):
    """Test qu'un agent appartenant à la structure créatrice d'une fiche
    peut modifier la visibilité de cette fiche (passer en local) si elle est en visibilité brouillon"""
    fiche_zone.createur = mocked_authentification_user.agent.structure
    fiche_zone.save()
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("link", name="Modifier la visibilité")).to_be_visible()
    page.get_by_role("link", name="Modifier la visibilité").click()
    page.get_by_text("Local").click()
    page.get_by_role("button", name="Valider").click()
    expect(
        page.get_by_role("heading", name="La visibilité de la fiche zone délimitée a bien été modifiée")
    ).to_be_visible()
    expect(page.get_by_text(Visibilite.LOCAL)).to_be_visible()
    fiche_zone.refresh_from_db()
    assert fiche_zone.visibilite == Visibilite.LOCAL


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCAL, Visibilite.NATIONAL])
def test_agent_in_structure_createur_cannot_update_fiche_zone_delimitee_visibilite(
    live_server, page: Page, fiche_zone, mocked_authentification_user, visibilite_libelle: str
):
    """Test qu'un agent appartenant à la structure créatrice d'une fiche
    ne peut pas modifier la visibilité de cette fiche si elle est en visibilité local ou national"""
    _update_visibilite_fiche(fiche_zone, visibilite_libelle)
    fiche_zone.createur = mocked_authentification_user.agent.structure
    fiche_zone.save()
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    expect(page.get_by_text("Modifier la visibilité")).not_to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_update_fiche_zone_delimitee_visibilite_local_to_national(
    live_server, page: Page, fiche_zone, mocked_authentification_user, structure_ac: str
):
    """Test qu'un agent appartenant à l'AC peut modifier la visibilité d'une fiche de local à national"""
    _update_visibilite_fiche(fiche_zone, Visibilite.LOCAL)
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("link", name="Modifier la visibilité")).to_be_visible()
    page.get_by_role("link", name="Modifier la visibilité").click()
    page.get_by_text("National").click()
    page.get_by_role("button", name="Valider").click()
    expect(
        page.get_by_role("heading", name="La visibilité de la fiche zone délimitée a bien été modifiée")
    ).to_be_visible()
    expect(page.get_by_text(Visibilite.NATIONAL, exact=True)).to_be_visible()
    fiche_zone.refresh_from_db()
    assert fiche_zone.visibilite == Visibilite.NATIONAL


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_update_fiche_zone_delimitee_visibilite_national_to_local(
    live_server, page: Page, fiche_zone, mocked_authentification_user, structure_ac: str
):
    """Test qu'un agent appartenant à l'AC peut modifier la visibilité d'une fiche de national à local"""
    _update_visibilite_fiche(fiche_zone, Visibilite.NATIONAL)
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("link", name="Modifier la visibilité")).to_be_visible()
    page.get_by_role("link", name="Modifier la visibilité").click()
    page.get_by_text("Local").click()
    page.get_by_role("button", name="Valider").click()
    expect(
        page.get_by_role("heading", name="La visibilité de la fiche zone délimitée a bien été modifiée")
    ).to_be_visible()
    expect(page.get_by_text(Visibilite.LOCAL, exact=True)).to_be_visible()
    fiche_zone.refresh_from_db()
    assert fiche_zone.visibilite == Visibilite.LOCAL

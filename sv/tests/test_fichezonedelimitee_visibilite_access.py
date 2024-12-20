import pytest
from django.urls import reverse
from model_bakery import baker
from playwright.sync_api import Page, expect
from core.models import Structure, Visibilite
from core.constants import BSV_STRUCTURE, MUS_STRUCTURE, AC_STRUCTURE
from sv.models import FicheZoneDelimitee, OrganismeNuisible, StatutReglementaire


def _update_visibilite_fiche(fiche, visibilite_libelle):
    fiche.visibilite = visibilite_libelle
    fiche.save()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_cannot_view_fiche_zone_delimitee_brouillon(live_server, page: Page):
    """Test qu'un agent n'appartenant pas à la structure créatrice d'une fiche ne peut pas voir la fiche
    si elle est en visibilité brouillon"""
    fiche_zone = FicheZoneDelimitee.objects.create(
        visibilite=Visibilite.BROUILLON,
        createur=baker.make(Structure),
        organisme_nuisible=baker.make(OrganismeNuisible),
        statut_reglementaire=baker.make(StatutReglementaire),
    )
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    expect(page.get_by_text("403 Forbidden")).to_be_visible()


def test_agent_not_in_structure_createur_cannot_view_fiche_zone_delimitee_local(live_server, page: Page):
    """Test qu'un agent n'appartenant pas à la structure créatrice d'une fiche ne peut pas voir la fiche
    si elle est en visibilité local"""
    fiche_zone = FicheZoneDelimitee.objects.create(
        visibilite=Visibilite.LOCAL,
        createur=baker.make(Structure),
        organisme_nuisible=baker.make(OrganismeNuisible),
        statut_reglementaire=baker.make(StatutReglementaire),
    )
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    expect(page.get_by_text("403 Forbidden")).to_be_visible()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_can_view_fiche_zone_delimitee_nationale(
    live_server, page: Page, fiche_zone, mocked_authentification_user
):
    """Test qu'un agent n'appartenant pas à la structure créatrice d'une fiche peut voir la fiche
    si elle est en visibilité national"""
    _update_visibilite_fiche(fiche_zone, Visibilite.NATIONAL)
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Fiche zone délimitée" f" n° {str(fiche_zone.numero)}")).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_cannot_view_fiche_zone_delimitee_brouillon(
    live_server, page: Page, mocked_authentification_user, structure_ac: str
):
    """Test qu'un agent appartenant à l'AC ne peut pas voir une fiche en visibilité brouillon"""
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    fiche_zone = FicheZoneDelimitee.objects.create(
        visibilite=Visibilite.BROUILLON,
        createur=baker.make(Structure),
        organisme_nuisible=baker.make(OrganismeNuisible),
        statut_reglementaire=baker.make(StatutReglementaire),
    )
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    expect(page.get_by_text("403 Forbidden")).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCAL, Visibilite.NATIONAL])
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_view_fiche_zone_delimitee(
    live_server,
    page: Page,
    fiche_zone,
    mocked_authentification_user,
    visibilite_libelle: str,
    structure_ac: str,
):
    """Test qu'un agent appartenant à l'AC peut voir une fiche en visibilité local ou national"""
    _update_visibilite_fiche(fiche_zone, visibilite_libelle)
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Fiche zone délimitée n° {str(fiche_zone.numero)}")).to_be_visible()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_cannot_view_fiche_zone_delimitee_brouillon_in_list_view(
    live_server, page: Page, mocked_authentification_user
):
    fiche_zone = FicheZoneDelimitee.objects.create(
        visibilite=Visibilite.BROUILLON,
        createur=baker.make(Structure),
        organisme_nuisible=baker.make(OrganismeNuisible),
        statut_reglementaire=baker.make(StatutReglementaire),
    )
    page.goto(f"{live_server.url}{reverse('fiche-liste')}?type_fiche=zone")
    expect(page.get_by_text(str(fiche_zone.numero))).not_to_be_visible()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_cannot_view_fiche_zone_delimitee_local_in_list_view(
    live_server, page: Page, fiche_zone, mocked_authentification_user
):
    fiche_zone = FicheZoneDelimitee.objects.create(
        visibilite=Visibilite.LOCAL,
        createur=baker.make(Structure),
        organisme_nuisible=baker.make(OrganismeNuisible),
        statut_reglementaire=baker.make(StatutReglementaire),
    )
    page.goto(f"{live_server.url}{reverse('fiche-liste')}?type_fiche=zone")
    expect(page.get_by_text(str(fiche_zone.numero))).not_to_be_visible()

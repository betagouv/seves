from datetime import datetime
import pytest
from model_bakery import baker
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.utils.timezone import make_aware

from core.models import Visibilite
from seves import settings
from ..models import (
    Region,
    OrganismeNuisible,
    Etat,
    FicheDetection,
    NumeroFiche,
    Departement,
    Lieu,
    ZoneInfestee,
)


def get_fiche_detection_search_form_url() -> str:
    return reverse("fiche-liste")


def test_search_form_have_all_fields(live_server, page: Page) -> None:
    """Test que le formulaire de recherche de fiche de détection contient tous les champs nécessaires."""
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    expect(page.get_by_role("heading", name="Rechercher une fiche")).to_be_visible()
    expect(page.get_by_text("Numéro")).to_be_visible()
    expect(page.get_by_label("Numéro")).to_be_visible()
    expect(page.get_by_label("Numéro")).to_be_empty()
    expect(page.locator("#search-form").get_by_text("Région")).to_be_visible()
    expect(page.get_by_label("Région")).to_be_visible()
    expect(page.get_by_label("Région")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_text("Organisme", exact=True)).to_be_visible()
    expect(page.locator(".choices__list--single .choices__placeholder")).to_be_visible()
    expect(page.locator(".choices__list--single .choices__placeholder")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_text("Période du")).to_be_visible()
    expect(page.get_by_label("Période du")).to_be_visible()
    expect(page.get_by_label("Période du")).to_be_empty()
    expect(page.get_by_text("Au", exact=True)).to_be_visible()
    expect(page.get_by_label("Au")).to_be_visible()
    expect(page.get_by_label("Au")).to_be_empty()
    expect(page.locator("#search-form").get_by_text("État")).to_be_visible()
    expect(page.get_by_label("État")).to_be_visible()
    expect(page.get_by_label("État")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_role("button", name="Effacer")).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


@pytest.mark.django_db
def test_reset_button_clears_form(live_server, page: Page, choice_js_fill) -> None:
    """Test que le bouton Effacer efface les champs du formulaire de recherche."""
    baker.make(Region, _quantity=5)
    baker.make(OrganismeNuisible, _quantity=5)
    baker.make(Etat, _quantity=5)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024")
    page.get_by_label("Région").select_option(index=1)
    organisme = OrganismeNuisible.objects.first().libelle_court
    choice_js_fill(page, ".choices__list--single", organisme, organisme)
    page.get_by_label("Période du").fill("2024-06-19")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_label("État").select_option(index=1)
    page.get_by_role("button", name="Effacer").click()

    expect(page.get_by_label("Numéro")).to_be_empty()
    expect(page.get_by_label("Région")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_label("Organisme")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_label("Période du")).to_be_empty()
    expect(page.get_by_label("Au")).to_be_empty()
    expect(page.get_by_label("État")).to_contain_text(settings.SELECT_EMPTY_CHOICE)


@pytest.mark.django_db
def test_reset_button_clears_form_when_filters_in_url(live_server, page: Page, choice_js_fill) -> None:
    """Test que le bouton Effacer efface les champs du formulaire de recherche."""
    baker.make(Region, _quantity=2)
    baker.make(OrganismeNuisible, _quantity=2)
    baker.make(Etat, _quantity=2)
    on = OrganismeNuisible.objects.first()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?organisme_nuisible={on.pk}")
    expect(page.get_by_label("Organisme")).to_contain_text(on.libelle_court)
    page.get_by_role("button", name="Effacer").click()

    expect(page.get_by_label("Organisme")).to_contain_text(settings.SELECT_EMPTY_CHOICE)


@pytest.mark.django_db
def test_search_with_fiche_number(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant un numéro de fiche valide (format année.numéro)"""
    num1 = NumeroFiche.get_next_numero()
    num2 = NumeroFiche.get_next_numero()
    baker.make(
        FicheDetection,
        numero=num1,
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
        visibilite=Visibilite.LOCAL,
    )
    baker.make(
        FicheDetection,
        numero=num2,
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
        visibilite=Visibilite.LOCAL,
    )

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill(str(num1))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(num1))).to_be_visible()


def test_search_with_invalid_fiche_number(client):
    """Test la recherche d'une fiche détection en utilisant un numéro de fiche invalide (format année.numéro)"""
    response = client.get(reverse("fiche-liste"), {"numero": "az.erty"})
    assert response.status_code == 200
    assert "numero" in response.context["form"].errors  # Le formulaire doit contenir une erreur pour le champ 'numero'
    assert (
        str(response.context["form"].errors["numero"][0]) == "Format 'numero' invalide. Il devrait être 'annee.numero'"
    )


def test_search_with_region(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une région
    Effectuer une recherche en sélectionnant uniquement une région.
    Vérifier que tous les résultats retournés sont bien associés à cette région."""
    region1, region2 = baker.make(Region, _quantity=2)
    fiche1 = baker.make(
        FicheDetection,
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
        visibilite=Visibilite.LOCAL,
    )
    baker.make(
        Lieu,
        departement=baker.make(Departement, region=region1),
        fiche_detection=fiche1,
    )
    baker.make(
        Lieu,
        departement=baker.make(Departement, region=region2),
        fiche_detection=baker.make(
            FicheDetection, etat=baker.make(Etat), createur=mocked_authentification_user.agent.structure
        ),
    )

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Région").select_option(str(region1.id))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche1.numero))).to_be_visible()


def test_search_with_organisme_nuisible(live_server, page: Page, mocked_authentification_user, choice_js_fill) -> None:
    """Test la recherche d'une fiche détection en utilisant un organisme nuisible.
    Effectue une recherche en sélectionnant un organisme nuisible spécifique et
    vérifier que les fiches détectées retournées sont associées à cet organisme."""
    organisme1, organisme2 = baker.make(OrganismeNuisible, _quantity=2)
    baker.make(
        FicheDetection,
        organisme_nuisible=organisme1,
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
    )
    baker.make(
        FicheDetection,
        organisme_nuisible=organisme2,
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
    )

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    choice_js_fill(page, ".choices__list--single", organisme1.libelle_court, organisme1.libelle_court)
    page.get_by_role("button", name="Rechercher").click()

    assert (
        page.url
        == f"{live_server.url}{reverse('fiche-liste')}?numero=&lieux__departement__region=&organisme_nuisible={organisme1.id}&start_date=&end_date=&etat="
    )

    expect(page.get_by_role("cell", name=organisme1.libelle_court)).to_be_visible()
    expect(page.get_by_role("cell", name=organisme2.libelle_court)).not_to_be_visible()


def test_search_with_period(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une période.
    Effectue une recherche en sélectionnant une période spécifique et
    vérifier que les fiches détectées retournées sont celles créées dans cette plage de dates."""
    fiche1 = baker.make(
        FicheDetection,
        date_creation=make_aware(datetime(2024, 6, 19)),
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
        visibilite=Visibilite.LOCAL,
    )
    fiche2 = baker.make(
        FicheDetection,
        date_creation=make_aware(datetime(2024, 6, 20)),
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
        visibilite=Visibilite.LOCAL,
    )

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Période du").fill("2024-06-19")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche2.numero))).not_to_be_visible()


def test_search_with_crossed_dates(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une période avec des dates croisées.
    Effectue une recherche en sélectionnant une période avec des dates croisées et
    vérifier que aucun résultat n'est retourné."""
    baker.make(
        FicheDetection,
        date_creation=make_aware(datetime(2024, 6, 19)),
        etat=baker.make(Etat),
        createur=mocked_authentification_user.agent.structure,
    )

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Période du").fill("2024-06-20")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.locator("body")).to_contain_text("0 fiches au total")


def test_search_with_state(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant un état.
    Effectue une recherche en sélectionnant un état spécifique et
    vérifier que les fiches détectées retournées sont celles ayant cet état."""
    etat1, etat2 = baker.make(Etat, _quantity=2)
    fiche1 = baker.make(
        FicheDetection, etat=etat1, createur=mocked_authentification_user.agent.structure, visibilite=Visibilite.LOCAL
    )
    fiche2 = baker.make(
        FicheDetection, etat=etat2, createur=mocked_authentification_user.agent.structure, visibilite=Visibilite.LOCAL
    )

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("État").select_option(str(etat1.id))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche2.numero))).not_to_be_visible()


def test_search_with_multiple_filters(live_server, page: Page, mocked_authentification_user, choice_js_fill) -> None:
    """Test la recherche d'une fiche détection en utilisant plusieurs filtres.
    Effectue une recherche en sélectionnant plusieurs filtres et
    vérifier que les fiches détectées retournées satisfont toutes les conditions spécifiées."""
    fiche1, fiche2 = baker.make(
        FicheDetection,
        etat=baker.make(Etat),
        _quantity=2,
        _fill_optional=True,
        createur=mocked_authentification_user.agent.structure,
        hors_zone_infestee=None,
        zone_infestee=None,
        visibilite=Visibilite.LOCAL,
    )
    lieu = baker.make(Lieu, fiche_detection=fiche1, _fill_optional=True)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Région").select_option(str(lieu.departement.region.id))
    organisme = fiche1.organisme_nuisible.libelle_court
    choice_js_fill(page, ".choices__list--single", organisme, organisme)
    page.get_by_label("Période du").fill(fiche1.date_creation.strftime("%Y-%m-%d"))
    page.get_by_label("Au").fill(fiche1.date_creation.strftime("%Y-%m-%d"))
    page.get_by_label("État").select_option(str(fiche1.etat.id))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche2.numero))).not_to_be_visible()


def test_search_without_filters(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection sans aucun filtre.
    Effectue une recherche sans entrer de critères dans les filtres pour s'assurer que tous les enregistrements sont retournés
    et qu'aucun filtre n'est appliqué."""
    fiche1, fiche2 = baker.make(
        FicheDetection,
        etat=baker.make(Etat),
        _quantity=2,
        createur=mocked_authentification_user.agent.structure,
        visibilite=Visibilite.LOCAL,
    )

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche2.numero))).to_be_visible()
    expect(page.locator("body")).to_contain_text("2 fiches au total")


def test_list_is_ordered(live_server, page, fiche_detection_bakery):
    fiche_1 = fiche_detection_bakery()
    numero = fiche_1.numero
    numero.annee = 2024
    numero.numero = 30
    numero.save()

    fiche_2 = fiche_detection_bakery()
    numero = fiche_2.numero
    numero.annee = 2023
    numero.numero = 7
    numero.save()

    fiche_3 = fiche_detection_bakery()
    numero = fiche_3.numero
    numero.annee = 2024
    numero.numero = 31
    numero.save()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(2) a"
    assert page.text_content(cell_selector).strip() == "2024.31"

    cell_selector = ".fiches__list-row:nth-child(2) td:nth-child(2) a"
    assert page.text_content(cell_selector).strip() == "2024.30"

    cell_selector = ".fiches__list-row:nth-child(3) td:nth-child(2) a"
    assert page.text_content(cell_selector).strip() == "2023.7"


def test_search_fiche_zone(live_server, page: Page, fiche_detection_bakery, fiche_zone_bakery):
    fiche_1 = fiche_detection_bakery()
    fiche_2 = fiche_zone_bakery()
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    expect(page.get_by_role("cell", name=str(fiche_1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.numero))).not_to_be_visible()

    page.get_by_text("Zone", exact=True).click()
    page.get_by_role("button", name="Rechercher").click()

    assert (
        page.url
        == f"{live_server.url}{reverse('fiche-liste')}?numero=&type_fiche=zone&lieux__departement__region=&organisme_nuisible=&start_date=&end_date=&etat="
    )

    expect(page.get_by_role("cell", name=str(fiche_1.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.numero))).to_be_visible()


def test_link_fiche_detection(live_server, page, fiche_detection_bakery, fiche_zone_bakery):
    fiche = fiche_detection_bakery()
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(9)"
    assert page.locator(cell_selector).inner_text().strip() == "Pas de zone"

    fiche_zone = fiche_zone_bakery()
    numero = fiche_zone.numero
    numero.annee = 2024
    numero.numero = 1
    numero.save()
    fiche.hors_zone_infestee = fiche_zone
    fiche.save()
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(9)"
    assert page.locator(cell_selector).inner_text().strip() == "2024.1"


def test_link_fiche_zone(live_server, page, fiche_zone_bakery, fiche_detection_bakery):
    fiche_zone = fiche_zone_bakery()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=zone")
    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(9)"
    assert page.locator(cell_selector).inner_text().strip() == "0"

    fiche = fiche_detection_bakery()
    fiche.hors_zone_infestee = fiche_zone
    fiche.save()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=zone")
    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(9)"
    assert page.locator(cell_selector).inner_text().strip() == "1"

    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone)
    for _ in range(2):
        detection = fiche_detection_bakery()
        detection.zone_infestee = zone_infestee
        detection.save()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=zone")
    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(9)"
    assert page.locator(cell_selector).inner_text().strip() == "3"

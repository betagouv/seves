import pytest
from django.urls import reverse
from model_bakery import baker
from playwright.sync_api import Page, expect

from seves import settings
from ..factories import FicheDetectionFactory, LieuFactory, FicheZoneFactory, EvenementFactory
from ..models import (
    Region,
    OrganismeNuisible,
    Lieu,
    ZoneInfestee,
    Evenement,
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
    on = OrganismeNuisible.objects.first()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?evenement__organisme_nuisible={on.pk}")
    expect(page.get_by_label("Organisme")).to_contain_text(on.libelle_court)
    page.get_by_role("button", name="Effacer").click()

    expect(page.get_by_label("Organisme")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    assert (
        page.url
        == f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=detection&numero=&lieux__departement__region=&evenement__organisme_nuisible=&start_date=&end_date=&evenement__etat="
    )


@pytest.mark.django_db
def test_search_with_fiche_number(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant un numéro de fiche valide (format année.numéro)"""
    FicheDetectionFactory(evenement__numero_annee=2024, evenement__numero_evenement=1, numero_detection="2024.1.1")
    FicheDetectionFactory(evenement__numero_annee=2024, evenement__numero_evenement=2, numero_detection="2024.1.2")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024.1.1")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name="2024.1.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.2.1")).not_to_be_visible()


@pytest.mark.django_db
def test_search_with_fiche_number_allows_year_only(live_server, page: Page, mocked_authentification_user):
    FicheDetectionFactory(numero_detection="2024.1.1")
    FicheDetectionFactory(numero_detection="2024.1.2")
    FicheDetectionFactory(numero_detection="2024.10.1")
    FicheDetectionFactory(numero_detection="2023.1.2")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name="2024.1.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.1.2")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.10.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2023.1.2")).not_to_be_visible()


@pytest.mark.django_db
def test_search_with_fiche_number_allows_year_and_first_char(live_server, page: Page, mocked_authentification_user):
    FicheDetectionFactory(numero_detection="2024.1.1")
    FicheDetectionFactory(numero_detection="2024.1.2")
    FicheDetectionFactory(numero_detection="2024.10.1")
    FicheDetectionFactory(numero_detection="2024.101.1")
    FicheDetectionFactory(numero_detection="2024.20.1")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024.1")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name="2024.1.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.1.2")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.10.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.101.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2023.20.2")).not_to_be_visible()


@pytest.mark.django_db
def test_search_with_fiche_number_allows_year_and_evenement_number(live_server, page, mocked_authentification_user):
    FicheDetectionFactory(numero_detection="2024.1.1")
    FicheDetectionFactory(numero_detection="2024.1.2")
    FicheDetectionFactory(numero_detection="2024.10.1")
    FicheDetectionFactory(numero_detection="2024.101.1")
    FicheDetectionFactory(numero_detection="2024.20.1")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024.1.")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name="2024.1.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.1.2")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.10.1")).not_to_be_visible()
    expect(page.get_by_role("cell", name="2024.101.1")).not_to_be_visible()
    expect(page.get_by_role("cell", name="2023.20.2")).not_to_be_visible()


def test_search_with_invalid_fiche_number(client):
    """Test la recherche d'une fiche détection en utilisant un numéro de fiche invalide (format année.numéro)"""
    response = client.get(reverse("fiche-liste") + "?numero=az.erty")
    assert response.status_code == 200
    assert "numero" in response.context["form"].errors  # Le formulaire doit contenir une erreur pour le champ 'numero'
    assert (
        str(response.context["form"].errors["numero"][0])
        == "Format 'numero' invalide. Le numéro doit commencer par quatre chiffres'"
    )


def test_search_with_region(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une région
    Effectuer une recherche en sélectionnant uniquement une région.
    Vérifier que tous les résultats retournés sont bien associés à cette région."""
    lieu = LieuFactory(departement__nom="Corse-du-Sud")
    other_lieu = LieuFactory(departement__nom="Ain")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Région").select_option("Corse")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(lieu.fiche_detection.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(other_lieu.fiche_detection.numero))).not_to_be_visible()


def test_search_with_organisme_nuisible(live_server, page: Page, mocked_authentification_user, choice_js_fill) -> None:
    """Test la recherche d'une fiche détection en utilisant un organisme nuisible.
    Effectue une recherche en sélectionnant un organisme nuisible spécifique et
    vérifier que les fiches détectées retournées sont associées à cet organisme."""
    organisme_1 = FicheDetectionFactory().evenement.organisme_nuisible
    organisme_2 = FicheDetectionFactory().evenement.organisme_nuisible

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    choice_js_fill(page, ".choices__list--single", organisme_1.libelle_court, organisme_1.libelle_court)
    page.get_by_role("button", name="Rechercher").click()

    assert (
        page.url
        == f"{live_server.url}{reverse('fiche-liste')}?type_fiche=detection&numero=&lieux__departement__region=&evenement__organisme_nuisible={organisme_1.id}&start_date=&end_date=&evenement__etat="
    )

    expect(page.get_by_role("cell", name=organisme_1.libelle_court)).to_be_visible()
    expect(page.get_by_role("cell", name=organisme_2.libelle_court)).not_to_be_visible()


def test_search_with_period(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une période.
    Effectue une recherche en sélectionnant une période spécifique et
    vérifier que les fiches détectées retournées sont celles créées dans cette plage de dates."""
    fiche_1 = FicheDetectionFactory(date_creation="2024-06-19")
    fiche_2 = FicheDetectionFactory(date_creation="2024-06-20")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Période du").fill("2024-06-19")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche_1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.numero))).not_to_be_visible()


def test_search_with_crossed_dates(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une période avec des dates croisées.
    Effectue une recherche en sélectionnant une période avec des dates croisées et
    vérifier que aucun résultat n'est retourné."""
    FicheDetectionFactory(date_creation="2024-06-19")
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Période du").fill("2024-06-20")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.locator("body")).to_contain_text("0 fiches au total")


def test_search_with_state(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant un état.
    Effectue une recherche en sélectionnant un état spécifique et
    vérifier que les fiches détectées retournées sont celles ayant cet état."""
    fiche_1 = FicheDetectionFactory(evenement__etat=Evenement.Etat.BROUILLON)
    fiche_2 = FicheDetectionFactory(evenement__etat=Evenement.Etat.CLOTURE)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("État").select_option("Clôturé")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche_1.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.numero))).to_be_visible()


def test_search_with_multiple_filters(live_server, page: Page, mocked_authentification_user, choice_js_fill) -> None:
    """Test la recherche d'une fiche détection en utilisant plusieurs filtres.
    Effectue une recherche en sélectionnant plusieurs filtres et
    vérifier que les fiches détectées retournées satisfont toutes les conditions spécifiées."""
    fiche1, fiche2 = FicheDetectionFactory.create_batch(2)
    lieu = baker.make(Lieu, fiche_detection=fiche1, _fill_optional=True)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Région").select_option(str(lieu.departement.region.id))
    organisme = fiche1.evenement.organisme_nuisible.libelle_court
    choice_js_fill(page, ".choices__list--single", organisme, organisme)
    page.get_by_label("Période du").fill(fiche1.date_creation.strftime("%Y-%m-%d"))
    page.get_by_label("Au").fill(fiche1.date_creation.strftime("%Y-%m-%d"))
    page.get_by_label("État").select_option(str(fiche1.evenement.etat))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche2.numero))).not_to_be_visible()


def test_search_without_filters(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection sans aucun filtre.
    Effectue une recherche sans entrer de critères dans les filtres pour s'assurer que tous les enregistrements sont retournés
    et qu'aucun filtre n'est appliqué."""
    fiche_1, fiche_2 = FicheDetectionFactory.create_batch(2)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche_1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.numero))).to_be_visible()
    expect(page.locator("body")).to_contain_text("2 fiches au total")


def test_list_is_ordered(live_server, page):
    FicheDetectionFactory(evenement__numero_annee=2023, evenement__numero_evenement=1, numero_detection="2023.1.7")
    FicheDetectionFactory(evenement__numero_annee=2024, evenement__numero_evenement=1, numero_detection="2024.1.30")
    FicheDetectionFactory(evenement__numero_annee=2024, evenement__numero_evenement=2, numero_detection="2024.2.31")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(2)"
    assert page.text_content(cell_selector).strip() == "2024.2.31"

    cell_selector = ".fiches__list-row:nth-child(2) td:nth-child(2)"
    assert page.text_content(cell_selector).strip() == "2024.1.30"

    cell_selector = ".fiches__list-row:nth-child(3) td:nth-child(2)"
    assert page.text_content(cell_selector).strip() == "2023.1.7"


def test_search_fiche_zone(live_server, page: Page):
    fiche_1 = FicheDetectionFactory()
    fiche_2 = FicheZoneFactory()
    EvenementFactory(fiche_zone_delimitee=fiche_2)
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    expect(page.get_by_role("cell", name=str(fiche_1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.evenement.numero))).not_to_be_visible()

    page.locator("label:has-text('Zone')").click()
    assert (
        page.url
        == f"{live_server.url}{reverse('fiche-liste')}?type_fiche=zone&numero=&evenement__organisme_nuisible=&start_date=&end_date=&evenement__etat="
    )

    expect(page.get_by_role("cell", name=str(fiche_1.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.evenement.numero))).to_have_count(2)


def test_link_fiche_detection(live_server, page: Page):
    fiche = FicheDetectionFactory()
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(10) input"
    expect(page.locator(cell_selector)).to_be_disabled()

    fiche_zone = FicheZoneFactory()
    evenement = fiche.evenement
    evenement.fiche_zone_delimitee = fiche_zone
    evenement.save()
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(10) input"
    expect(page.locator(cell_selector)).to_be_enabled()


def test_link_fiche_zone(live_server, page):
    fiche_zone = FicheZoneFactory()
    EvenementFactory(fiche_zone_delimitee=fiche_zone)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=zone")
    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(10)"
    assert page.locator(cell_selector).inner_text().strip() == "0"

    FicheDetectionFactory(hors_zone_infestee=fiche_zone)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=zone")
    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(10)"
    assert page.locator(cell_selector).inner_text().strip() == "1"

    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone)
    FicheDetectionFactory.create_batch(2, zone_infestee=zone_infestee)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=zone")
    cell_selector = ".fiches__list-row:nth-child(1) td:nth-child(10)"
    assert page.locator(cell_selector).inner_text().strip() == "3"


@pytest.mark.django_db
def test_cant_see_duplicate_fiche_detection_when_multiple_lieu_with_same_region(live_server, page: Page):
    """Test que lorsqu'une fiche de détection a plusieurs lieux dans la même région, elle n'apparaît qu'une seule fois dans la liste
    lors d'une recherche par région"""
    lieu = LieuFactory(departement__nom="Charente-Maritime")
    _other_lieu = LieuFactory(departement__nom="Charente-Maritime", fiche_detection=lieu.fiche_detection)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Région").select_option(str(lieu.departement.region.id))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(lieu.fiche_detection.numero))).to_have_count(1)


def test_cant_search_region_for_zone(live_server, page: Page):
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    expect(page.locator("#id_lieux__departement__region")).to_be_enabled()

    page.locator("label:has-text('Zone')").click()
    expect(page.locator("#id_lieux__departement__region")).to_be_disabled()

    page.get_by_role("button", name="Rechercher").click()

    page.wait_for_url(f"**{reverse('fiche-liste')}**")
    response = page.goto(page.url)
    assert response.status == 200


def test_cant_search_region_for_zone_on_page_load(live_server, page: Page):
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?type_fiche=zone")
    expect(page.locator("#id_lieux__departement__region")).to_be_disabled()


def test_form_is_auto_submitted_when_type_fiche_is_changed(live_server, page: Page):
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    page.locator("label:has-text('Zone')").click()
    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")

    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    page.locator("label:has-text('Détection')").click()
    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")

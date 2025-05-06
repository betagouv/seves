import pytest
from django.urls import reverse
from playwright.sync_api import Page, expect

from core.factories import ContactStructureFactory, ContactAgentFactory
from core.models import Contact
from seves import settings
from ..factories import (
    FicheDetectionFactory,
    LieuFactory,
    FicheZoneFactory,
    EvenementFactory,
    OrganismeNuisibleFactory,
    RegionFactory,
)
from ..models import (
    OrganismeNuisible,
    Evenement,
)


def get_fiche_detection_search_form_url() -> str:
    return reverse("sv:evenement-liste")


def test_search_form_have_all_fields(live_server, page: Page) -> None:
    """Test que le formulaire de recherche de fiche de détection contient tous les champs nécessaires."""
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    expect(page.get_by_role("heading", name="Rechercher un évènement")).to_be_visible()
    expect(page.get_by_label("Numéro évènement")).to_be_visible()
    expect(page.get_by_label("Numéro évènement")).to_be_empty()
    expect(page.locator("#search-form").get_by_text("Région")).to_be_visible()
    expect(page.get_by_label("Région")).to_be_visible()
    expect(page.get_by_label("Région")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_text("Organisme", exact=True)).to_be_visible()
    expect(page.locator("#id_organisme_nuisible ~ .choices__list--single .choices__placeholder")).to_be_visible()
    expect(page.locator("#id_organisme_nuisible ~ .choices__list--single .choices__placeholder")).to_contain_text(
        settings.SELECT_EMPTY_CHOICE
    )
    expect(page.get_by_label("Période du")).to_be_visible()
    expect(page.get_by_label("Période du")).to_be_empty()
    expect(page.get_by_label("Au")).to_be_visible()
    expect(page.get_by_label("Au")).to_be_empty()
    expect(page.locator("#search-form").get_by_text("État")).to_be_visible()
    expect(page.get_by_label("État")).to_be_visible()
    expect(page.get_by_label("État")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_label("Structure en contact")).to_be_visible()
    expect(page.get_by_label("Structure en contact")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_text("Agent en contact", exact=True)).to_be_visible()
    expect(page.locator("#id_agent_contact ~ .choices__list--single .choices__placeholder")).to_be_visible()
    expect(page.locator("#id_agent_contact ~ .choices__list--single .choices__placeholder")).to_contain_text(
        settings.SELECT_EMPTY_CHOICE
    )
    expect(page.get_by_role("button", name="Effacer")).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


@pytest.mark.django_db
def test_reset_button_clears_form(live_server, page: Page, choice_js_fill) -> None:
    """Test que le bouton Effacer efface les champs du formulaire de recherche."""
    RegionFactory.create_batch(5)
    OrganismeNuisibleFactory.create_batch(5)
    contact_structure = Contact.objects.filter(structure__isnull=False).first()
    contact_agent = Contact.objects.filter(agent__isnull=False).first()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024")
    page.get_by_label("Région").select_option(index=1)
    organisme = OrganismeNuisible.objects.first().libelle_court
    choice_js_fill(page, "#id_organisme_nuisible ~ .choices__list--single", organisme, organisme)
    page.get_by_label("Période du").fill("2024-06-19")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_label("État").select_option(index=1)
    page.get_by_label("Structure en contact").select_option(str(contact_structure.id))
    choice_js_fill(page, "#id_agent_contact ~ .choices__list--single", str(contact_agent), str(contact_agent))
    page.get_by_role("button", name="Effacer").click()

    expect(page.get_by_label("Numéro")).to_be_empty()
    expect(page.get_by_label("Région")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_label("Organisme")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.get_by_label("Période du")).to_be_empty()
    expect(page.get_by_label("Au")).to_be_empty()
    expect(page.get_by_label("État")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.locator("#id_structure_contact")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(page.locator("#id_agent_contact")).to_contain_text(settings.SELECT_EMPTY_CHOICE)


@pytest.mark.django_db
def test_reset_button_clears_form_when_filters_in_url(live_server, page: Page, choice_js_fill) -> None:
    """Test que le bouton Effacer efface les champs du formulaire de recherche."""
    RegionFactory.create_batch(2)
    OrganismeNuisibleFactory.create_batch(2)
    on = OrganismeNuisible.objects.first()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}?organisme_nuisible={on.pk}")
    expect(page.get_by_label("Organisme")).to_contain_text(on.libelle_court)
    page.get_by_role("button", name="Effacer").click()

    expect(page.get_by_label("Organisme")).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    assert (
        page.url
        == f"{live_server.url}{get_fiche_detection_search_form_url()}?numero=&region=&organisme_nuisible=&start_date=&end_date=&etat=&structure_contact=&agent_contact="
    )


@pytest.mark.django_db
def test_search_with_evenement_number(live_server, page: Page) -> None:
    """Test la recherche d'un évènement en utilisant un numéro d'évènement valide (format année.numéro)"""
    EvenementFactory(numero_annee=2024, numero_evenement=1)
    EvenementFactory(numero_annee=2024, numero_evenement=2)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024.1")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name="2024.1")).to_be_visible()
    expect(page.get_by_role("cell", name="2024.2")).not_to_be_visible()


@pytest.mark.django_db
def test_search_with_evenement_number_allows_year_only(live_server, page: Page):
    EvenementFactory(numero_annee=2024, numero_evenement=1)
    EvenementFactory(numero_annee=2024, numero_evenement=10)
    EvenementFactory(numero_annee=2023, numero_evenement=1)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Numéro").fill("2024")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name="2024.1", exact=True)).to_be_visible()
    expect(page.get_by_role("cell", name="2024.10")).to_be_visible()
    expect(page.get_by_role("cell", name="2023.1")).not_to_be_visible()


def test_search_with_invalid_evenement_number(live_server, page: Page):
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    numero_input = page.get_by_label("Numéro")

    numero_input.fill("az.erty")
    page.get_by_role("button", name="Rechercher").click()
    validation_message = numero_input.evaluate("el => el.validationMessage")
    assert validation_message in [
        "Please match the requested format.",
        "Le format attendu est AAAA ou AAAA.N (ex: 2025 ou 2025.1)",
    ]

    numero_input.fill("2025-15")
    page.get_by_role("button", name="Rechercher").click()
    validation_message = numero_input.evaluate("el => el.validationMessage")
    assert validation_message in [
        "Please match the requested format.",
        "Le format attendu est AAAA ou AAAA.N (ex: 2025 ou 2025.1)",
    ]


def test_search_with_region(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une région
    Effectuer une recherche en sélectionnant uniquement une région.
    Vérifier que tous les résultats retournés sont bien associés à cette région."""
    lieu = LieuFactory(departement__nom="Corse-du-Sud")
    other_lieu = LieuFactory(departement__nom="Ain")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Région").select_option("Corse")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(lieu.fiche_detection.evenement.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(other_lieu.fiche_detection.evenement.numero))).not_to_be_visible()


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
        == f"{live_server.url}{reverse('sv:evenement-liste')}?numero=&region=&organisme_nuisible={organisme_1.id}&start_date=&end_date=&etat=&structure_contact=&agent_contact="
    )

    expect(page.get_by_role("cell", name=organisme_1.libelle_court)).to_be_visible()
    expect(page.get_by_role("cell", name=organisme_2.libelle_court)).not_to_be_visible()


def test_search_with_organisme_nuisible_includes_sub_species(live_server, page: Page, choice_js_fill):
    organisme = OrganismeNuisibleFactory(libelle_court="Xylella fastidiosa")
    evenement_1 = EvenementFactory(organisme_nuisible=organisme)
    organisme_sub_specie = OrganismeNuisibleFactory(libelle_court="Xylella fastidiosa subsp. fastidiosa")
    evenement_2 = EvenementFactory(organisme_nuisible=organisme_sub_specie)
    evenement_3 = EvenementFactory()

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    choice_js_fill(
        page, "#id_organisme_nuisible ~.choices__list--single", organisme.libelle_court, organisme.libelle_court
    )
    page.get_by_role("button", name="Rechercher").click()

    assert (
        page.url
        == f"{live_server.url}{reverse('sv:evenement-liste')}?numero=&region=&organisme_nuisible={organisme.id}&start_date=&end_date=&etat=&structure_contact=&agent_contact="
    )

    expect(page.get_by_role("cell", name=evenement_1.numero)).to_be_visible()
    expect(page.get_by_role("cell", name=organisme.libelle_court, exact=True)).to_be_visible()
    expect(page.get_by_role("cell", name=evenement_2.numero)).to_be_visible()
    expect(page.get_by_role("cell", name=organisme_sub_specie.libelle_court)).to_be_visible()
    expect(page.get_by_role("cell", name=evenement_3.numero)).not_to_be_visible()
    expect(page.get_by_role("cell", name=evenement_3.organisme_nuisible.libelle_court)).not_to_be_visible()


def test_search_with_period(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une période.
    Effectue une recherche en sélectionnant une période spécifique et
    vérifier que les fiches détectées retournées sont celles créées dans cette plage de dates."""
    evenement_1 = EvenementFactory(date_creation="2024-06-19")
    evenement_2 = EvenementFactory(date_creation="2024-06-20")

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Période du").fill("2024-06-19")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(evenement_1.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(evenement_2.numero))).not_to_be_visible()


def test_search_with_crossed_dates(live_server, page: Page, mocked_authentification_user) -> None:
    """Test la recherche d'une fiche détection en utilisant une période avec des dates croisées.
    Effectue une recherche en sélectionnant une période avec des dates croisées et
    vérifier que aucun résultat n'est retourné."""
    EvenementFactory(date_creation="2024-06-19")
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Période du").fill("2024-06-20")
    page.get_by_label("Au").fill("2024-06-19")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_text("0 sur un total de 0")).to_be_visible()


def test_search_with_state(live_server, page: Page) -> None:
    """Test la recherche d'un évènement en utilisant un état.
    Effectue une recherche en sélectionnant un état spécifique et
    vérifier que les évènements retournés sont celles ayant cet état."""
    evenement_1 = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    evenement_2 = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("État").select_option("Clôturé")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(evenement_1.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(evenement_2.numero))).to_be_visible()


def test_search_with_multiple_filters(live_server, page: Page, choice_js_fill) -> None:
    """Test la recherche d'un évènement en utilisant plusieurs filtres.
    Effectue une recherche en sélectionnant plusieurs filtres et
    vérifier que les évènements retournés satisfont toutes les conditions spécifiées."""
    fiche1, fiche2 = FicheDetectionFactory.create_batch(2)
    lieu = LieuFactory(fiche_detection=fiche1)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Région").select_option(str(lieu.departement.region.id))
    organisme = fiche1.evenement.organisme_nuisible.libelle_court
    choice_js_fill(page, ".choices__list--single", organisme, organisme)
    page.get_by_label("Période du").fill(fiche1.date_creation.strftime("%Y-%m-%d"))
    page.get_by_label("Au").fill(fiche1.date_creation.strftime("%Y-%m-%d"))
    page.get_by_label("État").select_option(str(fiche1.evenement.etat))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche1.evenement.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche2.evenement.numero))).not_to_be_visible()


def test_search_without_filters(live_server, page: Page) -> None:
    """Test la recherche d'un évènement sans aucun filtre.
    Effectue une recherche sans entrer de critères dans les filtres pour s'assurer que tous les enregistrements sont retournés
    et qu'aucun filtre n'est appliqué."""
    fiche_1, fiche_2 = FicheDetectionFactory.create_batch(2)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_role("button", name="Rechercher").click()

    expect(page.get_by_role("cell", name=str(fiche_1.evenement.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(fiche_2.evenement.numero))).to_be_visible()
    expect(page.get_by_text("2 sur un total de 2")).to_be_visible()


def test_zone_column(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    cell_selector = ".evenements__list-row:nth-child(1) td:nth-child(11) input"
    expect(page.locator(cell_selector)).to_be_disabled()

    fiche_zone = FicheZoneFactory()
    evenement.fiche_zone_delimitee = fiche_zone
    evenement.save()
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    cell_selector = ".evenements__list-row:nth-child(1) td:nth-child(11) input"
    expect(page.locator(cell_selector)).to_be_enabled()


def test_nb_fiches_detection_column(live_server, page: Page):
    evenement = EvenementFactory()
    cell_selector = ".evenements__list-row:nth-child(1) td:nth-child(10)"

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    assert page.locator(cell_selector).inner_text().strip() == "0"

    FicheDetectionFactory(evenement=evenement)
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    assert page.locator(cell_selector).inner_text().strip() == "1"

    FicheDetectionFactory.create_batch(2, evenement=evenement)
    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
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

    expect(page.get_by_role("cell", name=str(lieu.fiche_detection.evenement.numero))).to_have_count(1)


def test_filter_deleted_detection_in_count_column(live_server, page):
    evenement = EvenementFactory()
    FicheDetectionFactory(evenement=evenement)
    FicheDetectionFactory(evenement=evenement, is_deleted=True)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")

    assert page.locator(".evenements__list-row:nth-child(1) td:nth-child(10)").inner_text().strip() == "1"


def test_search_with_structure_contact(live_server, page: Page):
    evenement_1 = EvenementFactory()
    evenement_2 = EvenementFactory()
    contact_structure = ContactStructureFactory(with_one_active_agent=True)
    evenement_2.contacts.add(contact_structure)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    page.get_by_label("Structure en contact").select_option(str(contact_structure.id))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.locator(".evenements__list-row")).to_have_count(1)
    expect(page.get_by_role("cell", name=str(evenement_1.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(evenement_2.numero))).to_be_visible()


def test_search_with_agent_contact(live_server, page: Page, choice_js_fill):
    evenement_1 = EvenementFactory()
    evenement_2 = EvenementFactory()
    contact_agent = ContactAgentFactory(with_active_agent=True)
    evenement_2.contacts.add(contact_agent)

    page.goto(f"{live_server.url}{get_fiche_detection_search_form_url()}")
    choice_js_fill(page, "#id_agent_contact ~ .choices__list--single", str(contact_agent), str(contact_agent))
    page.get_by_role("button", name="Rechercher").click()

    expect(page.locator(".evenements__list-row")).to_have_count(1)
    expect(page.get_by_role("cell", name=str(evenement_1.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(evenement_2.numero))).to_be_visible()

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from core.models import Agent, Structure, Document, Visibilite
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from playwright.sync_api import Page
from model_bakery import baker
from model_bakery.recipe import Recipe, foreign_key
from sv.models import Etat, FicheDetection, FicheZoneDelimitee, StatutReglementaire

User = get_user_model()


@pytest.fixture
def form_elements(page: Page):
    return FicheDetectionFormDomElements(page)


@pytest.fixture
def lieu_form_elements(page: Page):
    return LieuFormDomElements(page)


@pytest.fixture
def prelevement_form_elements(page: Page):
    return PrelevementFormDomElements(page)


def check_select_options(page, label, expected_options):
    options = page.locator(f"label:has-text('{label}') ~ select option").element_handles()
    option_texts = [option.inner_text() for option in options]
    assert (
        option_texts == ["---------"] + expected_options
    ), f"Les options pour {label} ne correspondent pas aux options attendues"


@pytest.fixture(autouse=True)
def add_basic_etat_objects():
    # Normalement fait dans la migration 0007 mais ne sera toujours présent dans les tests à cause de la mécanique
    # de rollback de pytest
    Etat.objects.get_or_create(libelle="nouveau")
    Etat.objects.get_or_create(libelle="en cours")
    Etat.objects.get_or_create(libelle="clôturé")


@pytest.fixture(autouse=True)
def add_status_reglementaire_objects():
    status = {
        "OQP": "organisme quarantaine prioritaire",
        "OQ": "organisme quarantaine",
        "OQZP": "organisme quarantaine zone protégée",
        "ORNQ": "organisme réglementée non quarantaine",
        "OTR": "organisme temporairement réglementé",
        "OE": "organisme émergent",
    }
    for code, libelle in status.items():
        StatutReglementaire.objects.get_or_create(code=code, libelle=libelle)


@pytest.fixture
def fiche_zone_bakery(db, mocked_authentification_user):
    etat = Etat.objects.get(id=Etat.get_etat_initial())

    def _fiche_zone_bakery():
        return baker.make(
            FicheZoneDelimitee,
            _fill_optional=True,
            createur=mocked_authentification_user.agent.structure,
            etat=etat,
        )

    return _fiche_zone_bakery


@pytest.fixture
def fiche_zone(fiche_zone_bakery):
    return fiche_zone_bakery()


@pytest.fixture
def fiche_detection_bakery(db, mocked_authentification_user):
    def _fiche_detection_bakery():
        etat = Etat.objects.get(id=Etat.get_etat_initial())
        return baker.make(
            FicheDetection,
            _fill_optional=True,
            etat=etat,
            createur=mocked_authentification_user.agent.structure,
            hors_zone_infestee=None,
            zone_infestee=None,
            visibilite=Visibilite.LOCAL,
        )

    return _fiche_detection_bakery


@pytest.fixture
def fiche_detection(fiche_detection_bakery):
    return fiche_detection_bakery()


@pytest.fixture
def document_recipe(fiche_detection_bakery, db):
    def _document_recipe():
        fiche = fiche_detection_bakery()
        content_type = ContentType.objects.get_for_model(fiche)
        agent_recipe = Recipe(Agent)
        structure_recipe = Recipe(Structure, libelle="Structure Test")
        return Recipe(
            Document,
            created_by=foreign_key(agent_recipe),
            created_by_structure=foreign_key(structure_recipe),
            content_type=content_type,
            object_id=fiche.pk,
            _create_files=True,
        )

    return _document_recipe


@pytest.fixture
def fill_commune(db, page: Page, choice_js_fill_from_element):
    def _fill_commune(page):
        element = page.locator(".fr-modal__content").locator("visible=true").locator(".choices__list--single")
        choice_js_fill_from_element(page, element, fill_content="Lille", exact_name="Lille (59)")

    return _fill_commune


@pytest.fixture(params=["fiche_detection_bakery", "fiche_zone_bakery"])
def fiche_variable(request, fiche_detection_bakery, fiche_zone_bakery):
    if request.param == "fiche_detection_bakery":
        return fiche_detection_bakery
    return fiche_zone_bakery

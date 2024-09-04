import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from core.models import Agent, Structure, Document
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from playwright.sync_api import Page
from model_bakery import baker
from model_bakery.recipe import Recipe, foreign_key
from sv.models import Etat, FicheDetection

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
        option_texts == ["----"] + expected_options
    ), f"Les options pour {label} ne correspondent pas aux options attendues"


@pytest.fixture(autouse=True)
def add_basic_etat_objects():
    # Normalement fait dans la migration 0007 mais ne sera toujours présent dans les tests à cause de la mécanique
    # de rollback de pytest
    Etat.objects.get_or_create(libelle="nouveau")
    Etat.objects.get_or_create(libelle="en cours")
    Etat.objects.get_or_create(libelle="clôturé")


@pytest.fixture
def fiche_detection_bakery(db):
    def _fiche_detection_bakery():
        etat = Etat.objects.get(id=Etat.get_etat_initial())
        return baker.make(FicheDetection, _fill_optional=True, etat=etat)

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

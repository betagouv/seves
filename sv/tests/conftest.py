import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from model_bakery import baker
from playwright.sync_api import Page

from sv.models import (
    FicheDetection,
    StatutReglementaire,
    Region,
    Departement,
)
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from ..constants import DEPARTEMENTS, REGIONS, STATUTS_REGLEMENTAIRES

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
    assert option_texts == [settings.SELECT_EMPTY_CHOICE] + expected_options, (
        f"Les options pour {label} ne correspondent pas aux options attendues"
    )


@pytest.fixture(autouse=True)
def add_status_reglementaire_objects():
    for code, libelle in STATUTS_REGLEMENTAIRES.items():
        StatutReglementaire.objects.get_or_create(code=code, libelle=libelle)


@pytest.fixture
def fiche_detection_bakery(db, mocked_authentification_user):
    def _fiche_detection_bakery():
        return baker.make(
            FicheDetection,
            _fill_optional=True,
            createur=mocked_authentification_user.agent.structure,
            hors_zone_infestee=None,
            zone_infestee=None,
        )

    return _fiche_detection_bakery


@pytest.fixture
def fiche_detection(fiche_detection_bakery):
    return fiche_detection_bakery()


@pytest.fixture
def fill_commune(db, page: Page, choice_js_fill_from_element):
    def _fill_commune(page):
        element = page.locator(".fr-modal__content").locator("visible=true").locator(".choices__list--single")
        choice_js_fill_from_element(page, element, fill_content="Lille", exact_name="Lille (59)")

    return _fill_commune


@pytest.fixture(autouse=True)
def create_departement_if_needed(db):
    for nom in REGIONS:
        Region.objects.get_or_create(nom=nom)
    for numero, nom, region_nom in DEPARTEMENTS:
        region = Region.objects.get(nom=region_nom)
        Departement.objects.get_or_create(numero=numero, nom=nom, region=region)

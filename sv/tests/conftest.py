import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page

from core.tests.conftest import create_departement_if_needed  # noqa F403

from sv.models import StatutReglementaire
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from ..constants import STATUTS_REGLEMENTAIRES

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


@pytest.fixture(autouse=True)
def add_status_reglementaire_objects():
    for code, libelle in STATUTS_REGLEMENTAIRES.items():
        StatutReglementaire.objects.get_or_create(code=code, libelle=libelle)


@pytest.fixture
def fill_commune(db, page: Page, choice_js_fill_from_element):
    def _fill_commune(page):
        element = page.locator(".fr-modal__content").locator("visible=true").locator(".commune .choices__list--single")
        choice_js_fill_from_element(page, element, fill_content="Lille", exact_name="Lille (59)")

    return _fill_commune


@pytest.fixture
def goto_contacts(db):
    def _goto_contacts(page):
        page.get_by_role("tab", name="Contacts").click()
        page.get_by_role("tab", name="Contacts").evaluate("el => el.scrollIntoView()")

    return _goto_contacts

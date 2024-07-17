import os
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from core.models import Agent, Structure, Contact
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from playwright.sync_api import Page
from model_bakery import baker

from sv.models import Etat, FicheDetection


@pytest.fixture
def page(page):
    timeout = 2_000
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)
    yield page


@pytest.fixture(scope="module", autouse=True)
def set_django_allow_async_unsafe():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture(autouse=True)
def mocked_authentification_user():
    user = baker.make(get_user_model(), email="test@example.com")
    structure = baker.make(Structure, niveau2="Structure Test", libelle="Structure Test")
    agent = Agent.objects.create(user=user, prenom="John", nom="Doe", structure=structure, structure_complete="AC/DC")
    Contact.objects.create(agent=agent, email="text@example.com")

    def mocked(self, request):
        request.user = user
        return self.get_response(request)

    with patch("seves.middlewares.LoginRequiredMiddleware.__call__", mocked):
        yield user


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
def fiche_detection_bakery():
    def _fiche_detection_bakery():
        etat = Etat.objects.get(id=Etat.get_etat_initial())
        return baker.make(FicheDetection, _fill_optional=True, etat=etat)

    return _fiche_detection_bakery


@pytest.fixture
def fiche_detection(fiche_detection_bakery):
    return fiche_detection_bakery()

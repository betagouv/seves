import os
import pytest
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements
from playwright.sync_api import Page


@pytest.fixture(scope="module", autouse=True)
def set_django_allow_async_unsafe():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture
def form_elements(page: Page):
    return FicheDetectionFormDomElements(page)


@pytest.fixture
def lieu_form_elements(page: Page):
    return LieuFormDomElements(page)

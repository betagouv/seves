import os
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from playwright.sync_api import expect

from core.factories import StructureFactory
from core.models import Agent, Contact

User = get_user_model()


@pytest.fixture
def page(page):
    timeout = 4_000
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)
    yield page


@pytest.fixture(autouse=True)
def set_django_allow_async_unsafe():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture(autouse=True)
def mocked_authentification_user(db):
    user = baker.make(get_user_model(), email="test@example.com")
    user.is_active = True
    user.save()
    structure = StructureFactory(niveau2="Structure Test", libelle="Structure Test")
    Contact.objects.create(structure=structure, email="structure_test@test.fr")
    agent = Agent.objects.create(user=user, prenom="John", nom="Doe", structure=structure, structure_complete="AC/DC")
    Contact.objects.create(agent=agent, email="text@example.com")

    def mocked(self, request):
        request.user = user
        return self.get_response(request)

    with patch("seves.middlewares.LoginRequiredMiddleware.__call__", mocked):
        yield user


@pytest.fixture
def choice_js_fill(db, page):
    def _choice_js_fill(page, locator, fill_content, exact_name):
        page.query_selector(locator).click()
        page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        page.locator("*:focus").fill(fill_content)
        page.get_by_role("option", name=exact_name, exact=True).click()

    return _choice_js_fill


@pytest.fixture
def choice_js_fill_from_element(db, page):
    def _choice_js_fill(page, element, fill_content, exact_name):
        element.click()
        page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        page.locator("*:focus").fill(fill_content)
        page.get_by_role("option", name=exact_name, exact=True).click()

    return _choice_js_fill


@pytest.fixture
def choice_js_cant_pick(db, page):
    def _choice_js_cant_pick(page, locator, fill_content, exact_name):
        page.query_selector(locator).click()
        page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        page.locator("*:focus").fill(fill_content)
        expect(page.get_by_role("option", name=exact_name, exact=True)).not_to_be_visible()

    return _choice_js_cant_pick


@pytest.fixture
def choice_js_option_disabled(db, page):
    def _choice_js_cant_pick(page, locator, exact_name):
        page.query_selector(locator).click()
        page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        element = page.locator(locator).locator("xpath=..").locator(".choices__item--choice")
        expect(element.get_by_role("option", name=exact_name, exact=True))

    return _choice_js_cant_pick

import os
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import resolve
from playwright.sync_api import expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import StructureFactory, UserFactory, ContactStructureFactory
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
def mocked_authentification_user(db, request):
    if "disable_mocked_authentification_user" in request.keywords:
        yield
    else:
        user = UserFactory(email="test@example.com")
        user.is_active = True
        user.save()
        structure = StructureFactory(niveau2="Structure Test", libelle="Structure Test")
        Contact.objects.create(structure=structure, email="structure_test@test.fr")
        agent = Agent.objects.create(
            user=user, prenom="John", nom="Doe", structure=structure, structure_complete="AC/DC"
        )
        Contact.objects.create(agent=agent, email="text@example.com")

        def mocked(self, request):
            request.user = user
            match = resolve(request.path_info)
            request.domain = match.app_name
            return self.get_response(request)

        with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked):
            yield user


@pytest.fixture
def choice_js_fill(db, page):
    def _choice_js_fill(page, locator, fill_content, exact_name, use_locator_as_parent_element=False):
        if use_locator_as_parent_element:
            page.locator(locator).locator("input.choices__input").click()
        else:
            page.query_selector(locator).click()
        page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        page.locator("*:focus").fill(fill_content)
        if use_locator_as_parent_element:
            list_element = page.locator(locator).locator(".choices__list")
            list_element.get_by_role("option", name=exact_name, exact=True).click()
        else:
            page.locator(".choices__list--dropdown .choices__list").get_by_role(
                "option", name=exact_name, exact=True
            ).click()

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


@pytest.fixture
def check_select_options():
    def _check_select_options(page, select_id, expected_options, with_default_value=True):
        options = page.locator(f"#{select_id} option").element_handles()
        visible_texts = []
        for option in options:
            style = option.get_attribute("style") or ""
            if "display: none" not in style:
                visible_texts.append(option.inner_text())

        if with_default_value:
            expected_options = [settings.SELECT_EMPTY_CHOICE] + expected_options

        assert visible_texts == expected_options, (
            f"Les options pour {select_id} ne correspondent pas aux options attendues"
        )

    return _check_select_options


@pytest.fixture
def mus_contact():
    return ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE, structure__libelle=MUS_STRUCTURE
    )

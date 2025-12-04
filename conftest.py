import contextlib
import os
import random
from datetime import datetime
from typing import Iterable, Any
from unittest.mock import patch

import pytest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.urls import resolve
from django.urls.base import reverse
from django.utils.timezone import localdate
from playwright.sync_api import expect, Page

from core.constants import DEPARTEMENTS, AC_STRUCTURE, MUS_STRUCTURE
from core.factories import StructureFactory, UserFactory, ContactStructureFactory
from core.models import Agent, Contact, Region, Departement

User = get_user_model()


class E2ETestNetworkError(Exception):
    pass


@pytest.fixture
def page(page: Page, request):
    timeout = 4_000
    with contextlib.suppress(TypeError, ValueError):
        timeout = int(os.getenv("PLAYWRIGHT_TIMEOUT"))
    page.set_default_navigation_timeout(timeout)
    page.set_default_timeout(timeout)

    _original_goto = page.goto

    def custom_goto(url, *args, **kwargs):
        logs = []
        page.on("console", lambda msg: logs.append(msg.text))
        result = _original_goto(url, *args, **kwargs)
        if "ERR_NETWORK_CHANGED" in " ".join(logs):
            raise E2ETestNetworkError
        return result

    page.goto = custom_goto
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
def choice_js_fill_from_element_with_value(db, page):
    def _choice_js_fill(page, element, choices):
        element.click()
        page.wait_for_selector("input:focus", state="visible", timeout=2_000)

        for fill_content, value in choices:
            page.locator("*:focus").fill(fill_content)
            page.locator(f"[data-value={value}]").click()

    return _choice_js_fill


@pytest.fixture
def choice_js_cant_pick(db, page):
    def _choice_js_cant_pick(page, locator, fill_content, exact_name):
        page.query_selector(locator).click()
        page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        page.locator("*:focus").fill(fill_content)
        page.wait_for_timeout(1000)
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
def choice_js_get_values(db, page):
    def _choice_js_get_values(page, locator):
        selected_options = page.locator(f'{locator} ~ div [aria-selected="true"]')
        texts = []
        for i in range(selected_options.count()):
            texts.append(selected_options.nth(i).inner_text())
        return texts

    return _choice_js_get_values


def _check_select_options_on_element(element, expected_options, with_default_value):
    options = element.locator("option").element_handles()
    visible_texts = []
    for option in options:
        style = option.get_attribute("style") or ""
        if "display: none" not in style:
            visible_texts.append(option.inner_text())

    if with_default_value:
        expected_options = [settings.SELECT_EMPTY_CHOICE] + expected_options

    assert visible_texts == expected_options, (
        f"Les options pour {element.get_attribute('id')} ne correspondent pas aux options attendues"
    )


@pytest.fixture
def check_select_options():
    def _check_select_options(page, select_id, expected_options, with_default_value=True):
        element = page.locator(f"#{select_id}")
        _check_select_options_on_element(element, expected_options, with_default_value)

    return _check_select_options


@pytest.fixture
def url_builder_for_list_ordering(live_server):
    def _get_url(order_by_key_name, direction, route):
        base_url = f"{live_server.url}{reverse(route)}"
        if direction == "desc":
            base_url += f"?order_by={order_by_key_name}&order_dir=asc"
        return base_url

    return _get_url


@pytest.fixture
def assert_events_order():
    def _assert_events_order(page, evenements, expected_order, column=2):
        for row_index, event_key in enumerate(expected_order, start=1):
            cell_content = page.text_content(
                f".evenements__list-row:nth-child({row_index}) td:nth-child({column})"
            ).strip()
            assert cell_content == evenements[event_key].numero, (
                f"L'événement à la ligne {row_index} devrait être {evenements[event_key].numero} mais est {cell_content}"
            )

    return _assert_events_order


DEPARTEMENTS_BY_NAME = {it[1]: it for it in DEPARTEMENTS}


@pytest.fixture
def check_select_options_from_element():
    return _check_select_options_on_element


@pytest.fixture
def ensure_departements(db):
    def _ensure_departements(*dpt_names):
        departements = []
        for dpt_name in dpt_names:
            numero, nom, region_name = DEPARTEMENTS_BY_NAME[dpt_name]
            region, _ = Region.objects.get_or_create(nom=region_name)
            dpt, _ = Departement.objects.get_or_create(numero=numero, defaults={"region": region, "nom": nom})
            departements.append(dpt)

        return departements

    return _ensure_departements


@pytest.fixture
def assert_models_are_equal():
    def _assert_models_are_equal(obj_1, obj_2, *, fields=None, to_exclude=None, ignore_array_order=False):
        to_exclude = to_exclude or []

        def _model_to_dict(model):
            if isinstance(model, dict):
                return model

            result = {}

            meta_fields = {f.name: f for f in model._meta.get_fields()}

            for k, v in model.__dict__.items():
                if fields and k not in fields or k in to_exclude:
                    continue

                if isinstance(meta_fields.get(k), ArrayField) and ignore_array_order:
                    result[k] = set(v)
                elif (choice_display := getattr(model, f"get_{k}_display", None)) and callable(choice_display):
                    # Case of a field with choices; using get_FOO_display() minimizes test failures
                    # due to comparing the enum object with its value
                    result[k] = choice_display()
                elif isinstance(v, datetime):
                    # Force comparing dates with same timezone
                    result[k] = localdate(v)
                else:
                    result[k] = v

            return result

        assert _model_to_dict(obj_1) == _model_to_dict(obj_2)

    return _assert_models_are_equal


@pytest.fixture
def choose_different_values():
    def _choose_different_values(items, exclude, *, k=1, singleton=False) -> list[Any] | Any:
        if k > 1 and singleton:
            raise ValueError(
                f"Parameters {k=} and {singleton=} are mutually exclusive. When using flat=True, k must not be set."
            )

        if isinstance(exclude, str) or not isinstance(exclude, Iterable):
            exclude = [exclude]

        result = random.sample([it for it in items if it not in exclude], k=k)
        return result[0] if singleton else result

    return _choose_different_values


@pytest.fixture
def mus_contact():
    return ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE, structure__libelle=MUS_STRUCTURE
    )

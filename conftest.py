import os
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from core.models import Agent, Structure, Contact
from model_bakery import baker

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
    structure = baker.make(Structure, niveau2="Structure Test", libelle="Structure Test")
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
        page.wait_for_selector("*:focus", state="visible", timeout=2_000)
        page.locator("*:focus").fill(fill_content)
        page.get_by_role("option", name=exact_name, exact=True).click()

    return _choice_js_fill

from django.core.cache import caches
import pytest


@pytest.fixture(autouse=True)
def locmem_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "pageview-ratelimit-tests",
        }
    }
    caches["default"].clear()
    yield
    caches["default"].clear()


class FakeUser:
    def __init__(self, pk=1, is_authenticated=True):
        self.pk = pk
        self.is_authenticated = is_authenticated


@pytest.fixture
def fake_user():
    return FakeUser()

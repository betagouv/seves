from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
import pytest

from rate_limit.middleware import PageViewRateLimitMiddleware
from rate_limit.tests.conftest import FakeUser

pytestmark = pytest.mark.urls("RATELIMIT.tests.urls")


def make_middleware(response_status=200):
    def get_response(request):
        return HttpResponse("ok", status=response_status)

    return PageViewRateLimitMiddleware(get_response)


def test_anonymous_users_are_never_rate_limited(settings, rf: RequestFactory):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 1}
    middleware = make_middleware()
    request = rf.get("/plain/")
    request.user = AnonymousUser()

    for _ in range(5):
        response = middleware(request)
        assert response.status_code == 200


def test_requests_under_the_limit_pass_through(settings, rf):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 3}
    middleware = make_middleware()
    request = rf.get("/plain/")
    request.user = FakeUser()

    for _ in range(3):
        response = middleware(request)
        assert response.status_code == 200


def test_requests_over_the_limit_are_rejected_with_dedicated_status_code(settings, rf):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 2, "STATUS_CODE": 429}
    middleware = make_middleware()
    request = rf.get("/plain/")
    request.user = FakeUser()

    assert middleware(request).status_code == 200
    assert middleware(request).status_code == 200
    blocked = middleware(request)

    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_disabled_middleware_never_blocks(settings, rf):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 0, "ENABLED": False}
    middleware = make_middleware()
    request = rf.get("/plain/")
    request.user = FakeUser()

    assert middleware(request).status_code == 200


@pytest.mark.parametrize("path", ["/static/logo.png"])
def test_excluded_path_prefix_is_never_counted_or_blocked(settings, rf, path):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 0, "EXCLUDED_PATH_PREFIXES": ["/static/"]}
    middleware = make_middleware()
    request = rf.get(path)
    request.user = FakeUser()

    for _ in range(5):
        assert middleware(request).status_code == 200


def test_excluded_namespace_is_never_counted_or_blocked(settings, rf):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 0, "EXCLUDED_NAMESPACES": ["excluded_group"]}
    middleware = make_middleware()
    request = rf.get("/group/a/")
    request.user = FakeUser()

    assert middleware(request).status_code == 200


def test_excluded_url_name_is_never_counted_or_blocked(settings, rf):
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 0, "EXCLUDED_URL_NAMES": ["named-exempt"]}
    middleware = make_middleware()
    request = rf.get("/named-exempt/")
    request.user = FakeUser()

    assert middleware(request).status_code == 200


def test_fails_open_when_cache_backend_cannot_increment(settings, rf):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    settings.RATELIMIT = {"MAX_REQUESTS_PER_HOUR": 0}
    middleware = make_middleware()
    request = rf.get("/plain/")
    request.user = FakeUser()

    for _ in range(5):
        assert middleware(request).status_code == 200

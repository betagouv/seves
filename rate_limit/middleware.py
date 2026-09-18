import logging

from django.http import HttpResponse
from django.urls import Resolver404, resolve

from rate_limit.conf import app_settings
from rate_limit.utils import increment_page_view_count

logger = logging.getLogger(__name__)


class PageViewRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not app_settings.ENABLED:
            return self.get_response(request)

        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return self.get_response(request)

        if self._is_exempt(request):
            return self.get_response(request)

        count = self._record_page_view(user)

        if count is not None and count > app_settings.MAX_REQUESTS_PER_HOUR:
            return HttpResponse(app_settings.RESPONSE_MESSAGE, status=app_settings.STATUS_CODE)

        return self.get_response(request)

    def _is_exempt(self, request):
        if any(request.path_info.startswith(prefix) for prefix in app_settings.EXCLUDED_PATH_PREFIXES):
            return True

        try:
            match = resolve(request.path_info)
        except Resolver404:
            return False

        if match.url_name in app_settings.EXCLUDED_URL_NAMES:
            return True

        return False

    def _record_page_view(self, user):
        try:
            return increment_page_view_count(user)
        except Exception:
            # Le rate limiting ne doit jamais faire tomber le site (ex: backend de cache
            # mal configuré, ou DummyCache qui ne supporte pas réellement `incr`).
            logger.warning("RATELIMIT: impossible d'utiliser le cache, requête laissée passer", exc_info=True)
            return None

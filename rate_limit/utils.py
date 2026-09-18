import time

from django.core.cache import caches

from rate_limit.conf import app_settings


def get_cache():
    return caches[app_settings.CACHE_ALIAS]


def build_cache_key(user_id):
    current_window = int(time.time() // app_settings.WINDOW_SECONDS)
    return f"{app_settings.CACHE_KEY_PREFIX}:{user_id}:{current_window}"


def get_page_view_count(user):
    return get_cache().get(build_cache_key(user.pk), 0)


def increment_page_view_count(user):
    cache = get_cache()
    cache_key = build_cache_key(user.pk)
    try:
        return cache.incr(cache_key)
    except ValueError:
        cache.add(cache_key, 0, timeout=app_settings.WINDOW_SECONDS)
        return cache.incr(cache_key)

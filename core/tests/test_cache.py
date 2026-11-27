from unittest import mock

from django.conf import settings
import pytest
import redis

from core.cache import MemoryGuardedRedisCache

KEYS = ["first", "second", "third"]


@pytest.fixture
def guarded_cache():
    cache = MemoryGuardedRedisCache(settings.CACHES["default"]["LOCATION"], {"KEY_PREFIX": "test-memory-guard"})
    cache.MEMORY_CHECK_INTERVAL = 0
    cache.delete_many(KEYS)
    yield cache
    cache.delete_many(KEYS)


def _redis_memory(used, maximum):
    return mock.patch.object(redis.Redis, "info", return_value={"used_memory": used, "maxmemory": maximum})


def test_memory_guarded_cache_skips_writes_above_max_memory_ratio(guarded_cache):
    with _redis_memory(used=79, maximum=100):
        guarded_cache.set("first", 1)

    with _redis_memory(used=80, maximum=100):
        guarded_cache.set("first", 2)
        assert guarded_cache.add("second", 1) is False
        assert guarded_cache.set_many({"third": 1}) == ["third"]

    assert guarded_cache.get_many(KEYS) == {"first": 1}

    with _redis_memory(used=79, maximum=0):
        guarded_cache.set("first", 2)
    with _redis_memory(used=MemoryGuardedRedisCache.DEFAULT_MAX_MEMORY, maximum=0):
        guarded_cache.set("first", 3)
    assert guarded_cache.get("first") == 2

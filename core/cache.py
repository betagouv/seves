import logging
import time

from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.redis import RedisCache

logger = logging.getLogger(__name__)


class MemoryGuardedRedisCache(RedisCache):
    """
    Skips writes once Redis memory goes above a ratio of its maximum, to leave free space for the Celery broker
    """

    MAX_MEMORY_RATIO = 0.8
    # Used when there is no maximum memory
    DEFAULT_MAX_MEMORY = 128 * 1024 * 1024
    MEMORY_CHECK_INTERVAL = 10  # seconds

    def __init__(self, server, params):
        super().__init__(server, params)
        self._last_memory_check = None
        self._has_room = True

    def _check_has_room(self):
        now = time.monotonic()
        if self._last_memory_check is not None and now - self._last_memory_check < self.MEMORY_CHECK_INTERVAL:
            return self._has_room

        self._last_memory_check = now
        info = self._cache.get_client(write=True).info("memory")
        max_memory = info["maxmemory"] or self.DEFAULT_MAX_MEMORY
        has_room = info["used_memory"] < self.MAX_MEMORY_RATIO * max_memory
        if self._has_room and not has_room:
            logger.error(
                "Redis memory is above %d%% of its limit, cache writes are skipped",
                self.MAX_MEMORY_RATIO * 100,
            )
        self._has_room = has_room
        return has_room

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        if not self._check_has_room():
            return False
        return super().add(key, value, timeout, version)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        if self._check_has_room():
            super().set(key, value, timeout, version)

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        if not self._check_has_room():
            return list(data)
        return super().set_many(data, timeout, version)

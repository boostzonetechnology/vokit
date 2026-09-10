from __future__ import annotations

from django.core.cache import cache


class CacheLoginRateLimiter:
    def __init__(self, *, limit: int = 8, window_seconds: int = 300) -> None:
        self._limit = limit
        self._window = window_seconds

    def allow(self, key: str) -> bool:
        current = cache.get(self._cache_key(key), 0)
        return int(current) < self._limit

    def register_failure(self, key: str) -> None:
        cache_key = self._cache_key(key)
        try:
            cache.incr(cache_key)
        except ValueError:
            cache.add(cache_key, 1, self._window)

    def reset(self, key: str) -> None:
        cache.delete(self._cache_key(key))

    def _cache_key(self, key: str) -> str:
        return f"identity.login.{key}"

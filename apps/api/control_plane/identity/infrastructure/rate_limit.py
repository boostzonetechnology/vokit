"""Cache-backed rate limiters (login + MFA/OTP). SEC-008.

Uses Django's default cache. LocMemCache is process-local (fine for single-worker
lab). Multi-worker / multi-host production must point CACHES at a shared backend
(Redis) so counters are coherent — see docs/flows/auth/MFA_FLOW.md.
"""

from __future__ import annotations

from django.core.cache import cache

from shared_kernel.errors import DomainError


class CacheKeyedRateLimiter:
    def __init__(
        self,
        *,
        prefix: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        self._prefix = prefix
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

    def consume(self, key: str) -> None:
        """Count a successful attempt toward the limit (e.g. OTP send)."""
        self.register_failure(key)

    def reset(self, key: str) -> None:
        cache.delete(self._cache_key(key))

    def assert_allowed(self, key: str) -> None:
        if not self.allow(key):
            raise DomainError(
                "rate_limited",
                "Too many attempts. Try again later.",
                http_status=429,
            )

    def assert_and_consume(self, key: str) -> None:
        self.assert_allowed(key)
        self.consume(key)

    def _cache_key(self, key: str) -> str:
        return f"{self._prefix}.{key}"


class CacheLoginRateLimiter(CacheKeyedRateLimiter):
    def __init__(self, *, limit: int = 8, window_seconds: int = 300) -> None:
        super().__init__(
            prefix="identity.login",
            limit=limit,
            window_seconds=window_seconds,
        )


# MFA / OTP — generous defaults; Phase C SEC-008 slice.
def mfa_send_limiter() -> CacheKeyedRateLimiter:
    """Email OTP send (login challenge + enroll)."""
    return CacheKeyedRateLimiter(
        prefix="identity.mfa.send",
        limit=5,
        window_seconds=600,
    )


def mfa_verify_limiter() -> CacheKeyedRateLimiter:
    """Failed MFA verify attempts (login challenge + confirm)."""
    return CacheKeyedRateLimiter(
        prefix="identity.mfa.verify",
        limit=10,
        window_seconds=300,
    )

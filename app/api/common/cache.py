"""
Response cache for public reference-data reads (categories, entity types, sources).

Wraps fastapi-cache2 with an in-memory backend: no Redis, one cache per worker
process. See specs/004-cache-reference-reads/ for the decisions behind it.
"""

import asyncio

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


class ReferenceCacheBackend(InMemoryBackend):
    """InMemoryBackend with a per-instance store.

    The library keeps ``_store`` and ``_lock`` at class level, so entries would
    leak across app instances (and across tests, which each start the app).
    """

    def __init__(self) -> None:
        self._store = {}
        self._lock = asyncio.Lock()


def init_cache() -> None:
    """Create a fresh, empty cache; called on every application startup.

    FastAPICache.init is a no-op when already initialised, hence the reset.
    """
    FastAPICache.reset()
    FastAPICache.init(ReferenceCacheBackend(), prefix="myths-cache")

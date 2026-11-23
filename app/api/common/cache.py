"""
Response cache for public reference-data reads (categories, entity types, sources).

Wraps fastapi-cache2 with an in-memory backend: no Redis, one cache per worker
process. See specs/004-cache-reference-reads/ for the decisions behind it.
"""

import asyncio
import json
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from starlette.requests import Request
from starlette.responses import Response

REFERENCE_TTL = 300  # categories and entity types: seconds
SOURCES_TTL = 60


class ReferenceCacheBackend(InMemoryBackend):
    """InMemoryBackend with a per-instance store that skips empty pages.

    The library keeps ``_store`` and ``_lock`` at class level, so entries would
    leak across app instances (and across tests, which each start the app).
    """

    def __init__(self) -> None:
        self._store = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        # Never store an empty page: the library only evicts an expired key when
        # it is read again, so `?page=N` over many N would grow memory without
        # bound. Only pages that exist are cached, which limits entries to the
        # real data (research.md R4).
        body = json.loads(value)
        if isinstance(body, dict) and body.get("items") == []:
            return
        await super().set(key, value, expire)


def reference_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    """Build the cache key from the endpoint and its validated parameters only.

    The library's default builder hashes ``str(kwargs)``, which includes the DB
    Session (its repr has a memory address), so every request would be a miss.
    Filtering by value type drops the Session without naming it, and ignores the
    raw query string, so unknown query params cannot create new entries.
    """
    params = {
        name: value.value if isinstance(value, Enum) else value
        for name, value in kwargs.items()
        if isinstance(value, (str, int, float, bool, Enum, type(None)))
    }
    return (
        f"{namespace}:{func.__module__}.{func.__qualname__}:"
        f"{json.dumps(params, sort_keys=True)}"
    )


def init_cache() -> None:
    """Create a fresh, empty cache; called on every application startup.

    FastAPICache.init is a no-op when already initialised, hence the reset.
    """
    FastAPICache.reset()
    FastAPICache.init(
        ReferenceCacheBackend(),
        prefix="myths-cache",
        key_builder=reference_key_builder,
    )

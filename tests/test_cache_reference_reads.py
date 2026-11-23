"""
Tests for the in-memory response cache on public reference-data reads
(specs/004-cache-reference-reads).
"""

import asyncio

from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache

from app.main import app


def _store(key: str, value: bytes) -> None:
    asyncio.run(FastAPICache.get_backend().set(key, value, 60))


def _read(key: str):
    return asyncio.run(FastAPICache.get_backend().get(key))


class TestCacheLifecycle:
    def test_should_start_each_application_startup_with_an_empty_cache(self):
        """The library keeps its store at class level, so without a fresh
        backend per startup, entries would leak across app instances (and
        across tests, since every test client runs the lifespan)."""
        with TestClient(app):
            _store("leaky-key", b"value")
            assert _read("leaky-key") == b"value"

        with TestClient(app):
            assert _read("leaky-key") is None

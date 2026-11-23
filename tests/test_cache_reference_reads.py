"""
Tests for the in-memory response cache on public reference-data reads
(specs/004-cache-reference-reads).
"""

import asyncio
import inspect

import pytest
from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from sqlalchemy.orm import Session

from app.api.v1.domains.entities.endpoints.categories import (
    get_category,
    list_categories,
)
from app.api.v1.domains.entities.endpoints.entity_types import (
    get_entity_type,
    list_entity_types,
)
from app.api.v1.domains.entities.endpoints.sources import get_source, list_sources
from app.api.v1.domains.entities.enums import CategoryName, EntityTypeName, SourceType
from app.api.v1.domains.entities.models.category import Category
from app.api.v1.domains.entities.models.entity import Entity
from app.api.v1.domains.entities.models.entity_type import EntityType
from app.api.v1.domains.entities.models.source import Source
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


# --- Helpers: one seeded row per cached resource ---------------------------------


def _seed(db: Session) -> dict:
    """Create one category, entity type and source; return what the tests need."""
    category = Category(name=CategoryName.MYTH, description="original")
    entity_type = EntityType(name=EntityTypeName.CHARACTER, description="original")
    db.add_all([category, entity_type])
    db.commit()
    entity = Entity(name="Zeus", category_id=category.id, entity_type_id=entity_type.id)
    db.add(entity)
    db.commit()
    source = Source(entity_id=entity.id, source_type=SourceType.BOOK, title="original")
    db.add(source)
    db.commit()
    return {
        "categories": (category, "description", "/api/v1/categories/", 300),
        "entity-types": (entity_type, "description", "/api/v1/entity-types/", 300),
        "sources": (source, "title", "/api/v1/sources/", 60),
    }


def _mutate(db: Session, row, field: str) -> None:
    setattr(row, field, "changed")
    db.commit()


def _body_field(body: dict, field: str, detail: bool):
    return body[field] if detail else body["items"][0][field]


RESOURCES = ["categories", "entity-types", "sources"]


class TestCachedReads:
    @pytest.mark.parametrize("resource", RESOURCES)
    def test_should_serve_list_from_cache_within_ttl(
        self, client: TestClient, db: Session, resource: str
    ):
        row, field, url, _ = _seed(db)[resource]

        first = client.get(url)
        _mutate(db, row, field)
        second = client.get(url)

        assert _body_field(first.json(), field, False) == "original"
        assert _body_field(second.json(), field, False) == "original"

    @pytest.mark.parametrize("resource", RESOURCES)
    def test_should_serve_detail_from_cache_within_ttl(
        self, client: TestClient, db: Session, resource: str
    ):
        row, field, url, _ = _seed(db)[resource]
        detail_url = f"{url}{row.id}"

        first = client.get(detail_url)
        _mutate(db, row, field)
        second = client.get(detail_url)

        assert _body_field(first.json(), field, True) == "original"
        assert _body_field(second.json(), field, True) == "original"

    @pytest.mark.parametrize("resource", RESOURCES)
    def test_should_advertise_the_configured_ttl_in_cache_control(
        self, client: TestClient, db: Session, resource: str
    ):
        _, _, url, ttl = _seed(db)[resource]

        response = client.get(url)

        assert response.headers.get("cache-control") == f"max-age={ttl}"

    def test_should_keep_stale_data_after_a_superuser_update_until_ttl(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Accepted staleness (spec Story 1, scenario 3): no invalidation on writes."""
        row, _, url, _ = _seed(db)["categories"]
        client.get(url)

        put = client.put(
            f"{url}{row.id}", json={"description": "renamed"}, headers=superuser_headers
        )
        after = client.get(url)

        assert put.status_code == 200
        assert after.json()["items"][0]["description"] == "original"

    @pytest.mark.parametrize(
        "fn",
        [
            list_categories,
            get_category,
            list_entity_types,
            get_entity_type,
            list_sources,
            get_source,
        ],
    )
    def test_should_keep_cached_endpoints_as_plain_def(self, fn):
        """Constitution IV: the endpoint source stays sync `def`; only the
        library wrapper is async (it runs the function in the threadpool)."""
        assert hasattr(fn, "__wrapped__"), "endpoint is not cached"
        assert not inspect.iscoroutinefunction(fn.__wrapped__)

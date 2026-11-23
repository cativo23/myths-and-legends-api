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
from app.core.config import settings
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
            _store("leaky-key", b'{"a": 1}')
            assert _read("leaky-key") == b'{"a": 1}'

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


def _entries() -> int:
    """Number of live entries in the active cache backend (our own subclass)."""
    return len(FastAPICache.get_backend()._store)


class TestCacheKeysAndErrors:
    def _seed_two_sources(self, db: Session) -> None:
        category = Category(name=CategoryName.MYTH, description="c")
        entity_type = EntityType(name=EntityTypeName.CHARACTER, description="t")
        db.add_all([category, entity_type])
        db.commit()
        entity = Entity(
            name="Zeus", category_id=category.id, entity_type_id=entity_type.id
        )
        db.add(entity)
        db.commit()
        db.add_all(
            [
                Source(entity_id=entity.id, source_type=SourceType.BOOK, title="A"),
                Source(entity_id=entity.id, source_type=SourceType.WEB, title="B"),
            ]
        )
        db.commit()

    @pytest.mark.parametrize(
        "query, expected_titles",
        [
            ("sort=title&order=asc", ["A", "B"]),
            ("sort=title&order=desc", ["B", "A"]),
            ("sort=title&size=1&page=1", ["A"]),
            ("sort=title&size=1&page=2", ["B"]),
            (f"source_type={SourceType.WEB.value}", ["B"]),
        ],
    )
    def test_should_return_data_matching_each_parameter_combination(
        self, client: TestClient, db: Session, query: str, expected_titles: list
    ):
        self._seed_two_sources(db)

        for _ in range(2):  # second call is served from the cache
            body = client.get(f"/api/v1/sources/?{query}").json()
            assert [item["title"] for item in body["items"]] == expected_titles

    def test_should_ignore_unknown_query_params_in_the_cache_key(
        self, client: TestClient, db: Session
    ):
        """Guard (FR-004): junk params must not create new cache entries."""
        self._seed_two_sources(db)
        client.get("/api/v1/sources/")
        baseline = _entries()

        client.get("/api/v1/sources/?foo=1")
        client.get("/api/v1/sources/?foo=2&bar=x")

        assert _entries() == baseline

    def test_should_not_cache_not_found_responses(
        self, client: TestClient, db: Session
    ):
        """Guard (FR-005): a 404 must not hide the row once it exists."""
        assert client.get("/api/v1/categories/1").status_code == 404
        db.add(Category(name=CategoryName.MYTH, description="now exists"))
        db.commit()

        assert client.get("/api/v1/categories/1").status_code == 200

    def test_should_not_cache_validation_errors(self, client: TestClient):
        """Guard (FR-005)."""
        assert client.get("/api/v1/categories/?size=0").status_code == 422
        assert _entries() == 0

    def test_should_return_same_body_for_anonymous_and_authenticated_callers(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Guard: the cache is shared, so the endpoints must not depend on the caller."""
        _seed(db)
        anonymous = client.get("/api/v1/categories/")
        authenticated = client.get("/api/v1/categories/", headers=auth_headers)

        assert anonymous.json() == authenticated.json()

    def test_should_not_cache_empty_pages(self, client: TestClient, db: Session):
        """Empty pages are not stored, so `page=N` cannot flood the cache."""
        empty = client.get("/api/v1/categories/")
        assert empty.json()["items"] == []
        assert _entries() == 0

        db.add(Category(name=CategoryName.MYTH, description="appears"))
        db.commit()
        assert len(client.get("/api/v1/categories/").json()["items"]) == 1

        before = _entries()
        beyond = client.get("/api/v1/categories/?page=99")
        assert beyond.json()["items"] == []
        assert _entries() == before


class TestCacheHeadersAndLimits:
    @pytest.mark.parametrize("call", [1, 2], ids=["miss", "hit"])
    def test_should_expose_cache_control_and_etag_but_not_cache_status_header(
        self, client: TestClient, db: Session, call: int
    ):
        _seed(db)
        for _ in range(call):
            response = client.get("/api/v1/categories/")

        assert response.headers["cache-control"].startswith("max-age=")
        assert response.headers["etag"].startswith("W/")
        assert "x-fastapi-cache" not in response.headers

    def test_should_return_304_when_if_none_match_matches_the_etag(
        self, client: TestClient, db: Session
    ):
        _seed(db)
        etag = client.get("/api/v1/categories/").headers["etag"]

        response = client.get("/api/v1/categories/", headers={"If-None-Match": etag})

        assert response.status_code == 304
        assert response.content == b""

    def test_should_keep_security_headers_cors_and_request_id_on_cached_responses(
        self, client: TestClient, db: Session
    ):
        _seed(db)
        origin = settings.BACKEND_CORS_ORIGINS[0]
        client.get("/api/v1/categories/")

        hit = client.get("/api/v1/categories/", headers={"Origin": origin})

        assert hit.headers["x-frame-options"] == "DENY"
        assert hit.headers["x-request-id"]
        assert hit.headers["access-control-allow-origin"] == origin

    def test_should_still_rate_limit_cached_endpoints(
        self, client: TestClient, db: Session
    ):
        _seed(db)
        statuses = [
            client.get("/api/v1/categories/").status_code
            for _ in range(settings.RATE_LIMIT_PER_MINUTE + 1)
        ]

        assert statuses[:-1] == [200] * settings.RATE_LIMIT_PER_MINUTE
        assert statuses[-1] == 429

    def test_should_refresh_when_client_sends_cache_control_no_cache(
        self, client: TestClient, db: Session
    ):
        """Documented library behavior: no-cache bypasses the cache (bounded by
        the rate limit)."""
        row, field, url, _ = _seed(db)["categories"]
        client.get(url)
        _mutate(db, row, field)

        refreshed = client.get(url, headers={"Cache-Control": "no-cache"})

        assert refreshed.json()["items"][0][field] == "changed"

    def test_should_fall_back_to_the_database_when_the_backend_fails(
        self, client: TestClient, db: Session, monkeypatch
    ):
        _seed(db)
        backend = FastAPICache.get_backend()

        async def boom(*args, **kwargs):
            raise RuntimeError("backend down")

        monkeypatch.setattr(backend, "get_with_ttl", boom)
        monkeypatch.setattr(backend, "set", boom)

        response = client.get("/api/v1/categories/")

        assert response.status_code == 200
        assert response.json()["items"][0]["description"] == "original"

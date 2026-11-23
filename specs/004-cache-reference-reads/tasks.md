---
description: "Task list for caching public reference-data reads"
---

# Tasks: Cache for public reference-data reads

**Input**: Design documents from `/specs/004-cache-reference-reads/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cache-headers.md, quickstart.md

**Tests**: REQUIRED (Constitution Principle I). Each story writes its tests first and sees them fail for the right reason. A few guard tests (marked *guard*) may already pass once an earlier task lands; they pin FR-004/FR-005 so a later change cannot regress them, and the task says so explicitly.

**Organization**: One commit per concern. Test file: `tests/test_cache_reference_reads.py`. Tests use the existing `client`, `db`, `superuser_headers`, `auth_headers` fixtures (SQLite). The cache module is `app/api/common/cache.py`. This feature adds no constrained fields (no DB change), so no `data-model.md` field citations are needed.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (dependencies and baseline)

- [ ] T001 Confirm baseline on the untouched branch: stack up (`./myths up -d`), `./myths test` green (331 passed, 85% expected), `uvx black --check app`
- [ ] T002 Add `fastapi-cache2>=0.2.2,<0.3` and `jinja2>=3.1,<4` to `requirements.in` (comment why jinja2: research.md R1), regenerate `requirements.txt` with `uv pip compile requirements.in --universal --python-version 3.10 --generate-hashes -o requirements.txt`, check the diff only adds `fastapi-cache2`, `jinja2`, `pendulum` (no unrelated bumps, no `redis`), rebuild the image (`./myths build`) and `./myths up -d`; verify `./myths python -c "import fastapi_cache"` works. Commit as `chore(deps): add fastapi-cache2 and jinja2 for response caching`

---

## Phase 2: Foundational (blocks every story)

**Purpose**: a fresh in-memory cache created at every application startup (FR-008, FR-012).

### Tests (write first, see them fail)

- [ ] T003 Create `tests/test_cache_reference_reads.py` with `should_start_each_application_startup_with_an_empty_cache`: inside one test, enter `with TestClient(app)` (import `app` from `app.main`, override `get_db` like the `client` fixture does, or reuse a helper in the test file), write an entry through `FastAPICache.get_backend().set(...)` (async: use `asyncio.run` or anyio), leave the context, enter a new one and assert the backend store is empty
- [ ] T004 Run it and confirm it fails for the right reason (`FastAPICache` not initialised: "You must call init first"). Commit as `test(cache): add startup isolation test for the response cache`

### Implementation

- [ ] T005 Create `app/api/common/cache.py` with `ReferenceCacheBackend(InMemoryBackend)` holding a per-instance `_store` and `_lock` (comment: the library keeps them at class level, so entries would leak across app instances and tests) and `init_cache()` doing `FastAPICache.reset()` then `FastAPICache.init(ReferenceCacheBackend(), prefix="myths-cache")`. Add `lifespan` (asynccontextmanager) to `app/main.py` calling `init_cache()` and `FastAPICache.reset()` on shutdown; pass `lifespan=lifespan` to `FastAPI(...)`. Run T003 until green, then the full suite quickly (`./myths test --no-cov`) to confirm nothing else broke. Commit as `feat(cache): initialise a fresh in-memory cache at app startup`

**Checkpoint**: cache exists but no endpoint uses it yet.

---

## Phase 3: User Story 1 - Repeated reads skip the database (Priority: P1)

**Goal**: the 6 public GETs are served from memory inside the TTL (FR-001, FR-002, FR-003, SC-001, SC-002).

**Independent Test**: change a row directly in the DB between two identical GETs; the second GET still returns the old value.

### Tests (write first, see them fail)

- [ ] T006 [US1] In `tests/test_cache_reference_reads.py` add, parametrised over categories, entity-types and sources: `should_serve_list_from_cache_within_ttl` (GET list, mutate the row via `db`, GET again: old body) and `should_serve_detail_from_cache_within_ttl` (same for `GET /{id}`)
- [ ] T007 [US1] Add `should_keep_stale_data_after_a_superuser_update_until_ttl` (GET category, PUT a new name with `superuser_headers`, GET again still shows the old name: accepted staleness, spec Story 1 scenario 3) and `should_advertise_the_configured_ttl_in_cache_control` (first response `Cache-Control: max-age=300` for categories and entity-types, `max-age=60` for sources)
- [ ] T008 [US1] Run the new tests and confirm they fail for the right reason (no caching yet: second GET returns fresh data; no `Cache-Control`). Commit as `test(cache): cover cached reads of reference data`

### Implementation

- [ ] T009 [US1] In `app/api/common/cache.py` add `REFERENCE_TTL = 300`, `SOURCES_TTL = 60` and `reference_key_builder(func, namespace, *, request, response, args, kwargs)`: key = `namespace:module.qualname:` + sorted JSON of kwargs whose values are `str|int|float|bool|None|Enum` (Enum by `.value`); filter by type so the `Session` is ignored by nature, not by name (comment: the default builder hashes the Session repr, so every request would miss; research.md R3). Pass it as `key_builder=` in `init_cache()`
- [ ] T010 [P] [US1] Add `@cache(expire=REFERENCE_TTL)` (from `fastapi_cache.decorator`) below `@router.get` on `list_categories` and `get_category` in `app/api/v1/domains/entities/endpoints/categories.py`; functions stay `def`
- [ ] T011 [P] [US1] Same for `list_entity_types` and `get_entity_type` in `entity_types.py`
- [ ] T012 [P] [US1] Same for `list_sources` and `get_source` in `sources.py` with `expire=SOURCES_TTL`
- [ ] T013 [US1] Run T006-T007 until green, then the files of the three domains (`./myths test tests/domains --no-cov`) to confirm existing endpoint tests still pass (cache cleared per client startup). Commit as `feat(cache): cache public reads of categories, entity types and sources`

**Checkpoint**: MVP. The cache works; Story 2 hardens it.

---

## Phase 4: User Story 2 - The cache never mixes up or grows without bound (Priority: P1)

**Goal**: correct keys, no error caching, bounded memory (FR-004, FR-005, FR-010, SC-003, SC-004).

**Independent Test**: vary parameters, add unknown query params, request missing ids and empty pages; verify responses and the backend store size.

### Tests (write first, see them fail)

- [ ] T014 [US2] Add `should_return_data_matching_each_parameter_combination` (different `page`, `size`, `sort`, `order`, `source_type` each return their own correct data after being cached) and `should_ignore_unknown_query_params_in_the_cache_key` (*guard*: `?foo=1` and `?foo=2` produce no new store entries; passes already if T009 is right)
- [ ] T015 [US2] Add `should_not_cache_not_found_responses` (*guard*: GET missing id gives 404, create it, GET gives 200), `should_not_cache_validation_errors` (*guard*: `size=0` gives 422 and the store stays empty) and `should_return_same_body_for_anonymous_and_authenticated_callers` (*guard*)
- [ ] T016 [US2] Add `should_not_cache_empty_pages`: request `?page=99` on a list (store stays empty), then create enough rows that page 99 would exist... simpler: GET list of an empty table, assert store empty, insert a row, GET again shows it
- [ ] T017 [US2] Run them; confirm `should_not_cache_empty_pages` fails for the right reason (empty page is stored, so the new row is hidden) and the *guard* tests pass. Commit as `test(cache): guard cache keys, error handling and empty pages`

### Implementation

- [ ] T018 [US2] In `ReferenceCacheBackend.set` in `app/api/common/cache.py` skip storing when the JSON body is a dict with `"items" == []` (comment: bounds memory, the library backend only evicts expired keys when re-read; research.md R4); otherwise delegate to `super().set`. Run T014-T016 until green. Commit as `fix(cache): do not cache empty pages to bound memory`

---

## Phase 5: User Story 3 - Revalidation, headers and limits (Priority: P2)

**Goal**: HTTP cache headers, no leaked cache state, rate limit and other middlewares intact (FR-006, FR-009, FR-011, SC-006).

**Independent Test**: inspect headers, send `If-None-Match`, exceed the rate limit.

### Tests (write first, see them fail)

- [ ] T019 [US3] Add `should_expose_cache_control_and_etag_but_not_cache_status_header` (hit and miss: `Cache-Control` and `ETag` present, `X-FastAPI-Cache` absent) and `should_return_304_when_if_none_match_matches_the_etag` (contract cache-headers.md)
- [ ] T020 [US3] Add `should_keep_security_headers_and_request_id_on_cached_responses`, `should_still_rate_limit_cached_endpoints` (loop `settings.RATE_LIMIT_PER_MINUTE + 1` GETs on a cached endpoint, last is 429; the autouse fixture resets the limiter) and `should_refresh_when_client_sends_cache_control_no_cache` (documented behaviour)
- [ ] T021 [US3] Add `should_fall_back_to_the_database_when_the_backend_fails`: make `get_with_ttl` and `set` of the active `ReferenceCacheBackend` raise (patch our own backend instance via `monkeypatch.setattr`, not the library) and assert the endpoint still returns 200 with correct data (FR-011)
- [ ] T022 [US3] Run them; confirm `should_expose_cache_control_and_etag_but_not_cache_status_header` fails for the right reason (`X-FastAPI-Cache` is present) and the rest pass as guards. Commit as `test(cache): cover cache headers, rate limiting and backend failure`

### Implementation

- [ ] T023 [US3] In `app/api/common/middleware/security_headers.py` remove `X-FastAPI-Cache` from every response (comment: do not reveal the cache state; the library offers no switch to turn the header off, research.md R5); update the module docstring. Run T019-T021 until green. Commit as `fix(cache): stop exposing the cache HIT/MISS header`

---

## Phase 6: Polish and cross-cutting

- [ ] T024 [P] Update `CHANGELOG.md` `[Unreleased]` (Added: response cache for categories, entity types and sources with TTLs and staleness note; closes #26) and `docs/ROADMAP.md` (mark 1.3 done, status line, notes: jinja2 hidden dependency, empty pages not cached, per-worker cache, `no-cache` bypass; keep the Redis/invalidation items out of scope). Commit as `docs(roadmap): close session 1.3 and record follow-ups`
- [ ] T025 Run `uvx black --check app`, then the full `./myths test` (coverage at or above the 68% gate), then quickstart.md manual steps against the running stack
- [ ] T026 Self-review the full diff as if written by someone else (secrets, keys, Constitution Check re-read, comments explain why); mark every task `[X]`; run `/speckit-analyze` before implementing and `/speckit-converge` after

---

## Dependencies

- T001 → T002 → Phase 2 → US1 → US2 → US3 → Polish. US2 and US3 depend on US1 (they need the cached endpoints) but not on each other, so US3 can go before US2 if preferred.
- T010, T011, T012 are parallel (different files).
- Within a story: tests, then see them red, then commit, then implement.

## Implementation strategy

MVP = Phase 1 + 2 + 3 (cache works, TTLs correct). Phases 4-5 are required before merging (they carry the security and memory guarantees); Polish closes the session.

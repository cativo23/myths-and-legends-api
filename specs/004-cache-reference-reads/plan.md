# Implementation Plan: Cache for public reference-data reads

**Branch**: `feature/cache-reference-reads` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-cache-reference-reads/spec.md`

## Summary

One new module, `app/api/common/cache.py`, wraps `fastapi-cache2`: a small in-memory backend
(`InMemoryBackend` subclass with a per-instance store that refuses to store empty pages), a key
builder that uses only primitive validated parameters, and `init_cache()`. The app gets a
`lifespan` that calls `init_cache()` (fresh backend on every startup, which also isolates tests).
The 6 public GETs of categories, entity-types and sources get `@cache(expire=...)` under their
`@router.get`; they stay `def`. `SecurityHeadersMiddleware` drops `X-FastAPI-Cache`. Dependency
`fastapi-cache2` is added with a cap, plus `jinja2` (hidden import, see research.md R1); the lock
is regenerated. No schema, model, service or response-shape change.

## Technical Context

**Language/Version**: Python 3.10 (Docker), CI matrix 3.10 / 3.11 / 3.12

**Primary Dependencies**: `fastapi-cache2>=0.2.2,<0.3` (new; pulls `pendulum`), `jinja2>=3.1,<4` (new direct pin: fastapi-cache2 imports `starlette.templating` at import time). No Redis.

**Storage**: in-process memory (per worker); PostgreSQL unchanged

**Testing**: pytest via `./myths test` (SQLite); new `tests/test_cache_reference_reads.py`

**Target Platform**: Linux container

**Project Type**: web-service (FastAPI)

**Performance Goals**: repeat read inside TTL = 0 DB queries on the 6 endpoints

**Constraints**: keys from validated params only; no error/empty-page caching; per-worker cache; weak ETag is `hash()` of the body so it changes across restarts/workers (client just gets one full 200)

**Scale/Scope**: 1 new module, 1 lifespan, 3 endpoint files (6 decorators), 1 middleware line, 2 requirements files, 1 test file, docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Test-First | PASS | Tests written first and seen failing (no caching yet). The library is wrapped in our own backend/key builder and that wrapper is what tests exercise; the library is not mocked |
| II. Security-First | PASS | Key from validated params only (no key flooding via junk params); empty pages and errors not cached (bounded memory); no per-user data in cache (endpoints are public and caller-independent); `X-FastAPI-Cache` not exposed; rate limiting still applies (tested). Residual: `Cache-Control: no-cache` forces refresh, bounded by rate limit |
| III. Minimalism | PASS | No Redis, no invalidation, no config flag, no entry cap, no custom decorator. Backend subclass is ~10 lines and exists only to bound memory |
| IV. Layered / sync | PASS (note) | Endpoint functions stay plain `def`. The library decorator is `async` internally but runs them via `run_in_threadpool`, exactly as FastAPI does for sync endpoints. Recorded in Complexity Tracking |
| V. Migrations | N/A | No schema change |

## Project Structure

### Documentation (this feature)

```text
specs/004-cache-reference-reads/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cache-headers.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
app/
├── main.py                                   # + lifespan calling init_cache()
├── api/common/
│   ├── cache.py                              # NEW: backend, key builder, TTL constants, init_cache()
│   └── middleware/security_headers.py        # drop X-FastAPI-Cache
└── api/v1/domains/entities/endpoints/
    ├── categories.py                         # @cache on GET / and GET /{id}
    ├── entity_types.py                       # same
    └── sources.py                            # same, 60 s
tests/test_cache_reference_reads.py           # NEW
requirements.in / requirements.txt            # new deps, regenerated lock
docs/ROADMAP.md, CHANGELOG.md                 # session 1.3 closed
```

**Structure Decision**: shared infrastructure goes in `app/api/common/` (like the rate limiter),
not in a domain; endpoints only add a decorator (stay thin).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Async wrapper around sync endpoints (Constitution IV wording) | It is how `fastapi-cache2` works; the sync `def` and `Session` are untouched and still run in the threadpool | Writing our own decorator would be more code than the library; dropping the cache leaves #26 open |
| `InMemoryBackend` subclass | Library backend never evicts unread expired keys and would cache empty pages (`page=N` key flood) | An entry-cap backend is more code; accepting the growth is a public-API memory risk |

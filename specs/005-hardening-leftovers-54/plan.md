# Implementation Plan: Hardening leftovers of issue #54

**Branch**: `fix/hardening-leftovers-54` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

## Summary

Validate `sort`/`order` (and countries `relations`) with allowed-value types on the three list endpoints that still take raw strings, make users and entities actually apply the ordering, and remove the default database password from compose. **No duplicated code (Carlos's directive):** the `getattr(Model, sort)` + asc/desc block already exists three times (categories, entity-types, sources); instead of copying it three more times, one shared helper and one `SortOrder` type are introduced and all six endpoints use them. Countries `relations` are defined once and shared by list and detail.

## Technical Context

**Language/Version**: Python 3.10 (lock target), FastAPI 0.135, Pydantic 2.x
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 sync `Session`, fastapi-pagination
**Storage**: PostgreSQL 15 (no schema change, no migration); tests run on SQLite
**Testing**: pytest via `./myths test` (full suite) and `./myths test <file> --no-cov`
**Target Platform**: Linux container (docker compose)
**Project Type**: web-service
**Performance Goals**: none new; sorting stays in SQL (countries move from Python `sorted` to `ORDER BY`)
**Constraints**: sync `def` endpoints, `HTTPException` envelope, no new dependencies
**Scale/Scope**: 3 list endpoints changed, 3 refactored to the helper, 1 compose line, README

## Constitution Check

| Principle | Status | Note |
|---|---|---|
| I Test-First | Pass | Every task writes the failing test first (422 cases, order across pages, compose config check) |
| II Security-First | Pass | Allowed-value validation at the boundary; no attribute names in errors; secure default for DB password |
| III Minimalism | Pass, justified | One small helper replaces 3 existing copies and prevents 3 more (explicit directive: no duplicated code). No config, no flags |
| IV Layered/sync | Pass | Endpoints stay `def`; ordering applied in the service/query layer; `Annotated` style |
| V Migrations | N/A | No schema change |

Re-checked after Phase 1 design: still passes.

## Design decisions (details in research.md)

1. `app/api/common/sorting.py`: `SortOrder = Literal["asc", "desc"]` and `apply_sort(stmt, model, sort, order)` that orders by the column with nulls last and adds `id` as tie-breaker. Each endpoint keeps only its own `Literal` of allowed fields.
2. `CRUDBaseService._build_query` accepts optional `sort`/`order` (default stays `id`), so `get_all`/`get_multi` (users, countries) reuse it; entities' `get_paginated` takes the same two arguments and calls the helper.
3. Countries `relations`: one `CountryRelations` Annotated type (comma list validated against {entities, locations}, `max_length=100`) used by list and detail; the Python `sorted(...)` in the endpoint is removed. `CountryService.get_multi` stays unlimited (the base one caps at 100): it only builds its query through `_build_query(relations, sort, order)` instead of its own `select`.
4. Compose: `${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required: set it in .env (see .env.example)}`; README row updated.

## Project Structure

### Documentation (this feature)

```text
specs/005-hardening-leftovers-54/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/list-query-params.md
└── tasks.md   # /speckit-tasks
```

### Source Code

```text
app/api/common/sorting.py                         # NEW: SortOrder + apply_sort
app/api/common/services/base_service.py           # _build_query(sort, order)
app/api/v1/domains/entities/endpoints/{categories,entity_types,sources}.py  # use helper (refactor)
app/api/v1/domains/entities/endpoints/entities.py + services/entity.py      # sort/order applied
app/api/v1/domains/countries/endpoints/countries.py + services/country.py   # Literal + relations
app/api/v1/domains/users/endpoints/users.py       # Literal + sort applied
docker-compose.yml, README.md
tests/test_sorting.py, tests/domains/test_{countries,users,entities}.py; .github/workflows/ci.yml (compose guard step)
```

**Structure Decision**: existing domain layout; the only new module is the shared `sorting.py` in `app/api/common/`.

## Commit plan (one concern per commit, tests with their code)

1. `refactor(api): share sort/order helper across list endpoints` (helper + categories/entity-types/sources, behavior preserved)
2. `fix(countries): validate sort, order and relations`
3. `fix(users): validate sort/order and apply ordering`
4. `fix(entities): validate sort/order and apply ordering`
5. `fix(compose): require POSTGRES_PASSWORD instead of a default` (+ CI guard step)
6. `docs(roadmap): close session 1.4` (+ deuda detectada)

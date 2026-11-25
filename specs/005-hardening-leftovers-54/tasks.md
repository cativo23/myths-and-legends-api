---
description: "Task list for hardening leftovers of issue #54"
---

# Tasks: Hardening leftovers of issue #54

**Input**: `/specs/005-hardening-leftovers-54/` (plan.md, spec.md, research.md, data-model.md, contracts/list-query-params.md, quickstart.md)

**Tests**: REQUIRED (Constitution Principle I). Each task writes its failing test first and confirms it fails for the right reason. Tests use the existing `client`, `db`, `superuser_headers`, `auth_headers` fixtures (SQLite). Do not run `black` on `tests/`.

**Organization**: One commit per concern (plan.md "Commit plan"); a task's tests and code go in the same commit. No code duplication: every endpoint uses `app/api/common/sorting.py`. No DB change, so no `data-model.md` field citations beyond the sortable-column table in data-model.md.

## Phase 1: Setup

- [X] T001 Baseline on the untouched branch: `./myths up -d`, `./myths test` green (365 passed expected), `uvx black --check app`

## Phase 2: Foundational (blocks every story) — commit `refactor(api): share sort/order helper across list endpoints`

- [X] T002 Write failing tests in `tests/test_sorting.py` for `apply_sort`: orders asc/desc by the given column, nulls last in both directions, adds `id` as tie-breaker (equal values come out in id order), and `SortOrder` accepts only asc/desc
- [X] T003 Create `app/api/common/sorting.py` with `SortOrder = Literal["asc", "desc"]` and `apply_sort(stmt, model, sort, order)` using `.nulls_last()` (research.md R1, R6); T002 turns green
- [X] T004 Replace the copied `getattr(...)`/asc/desc block and the inline `Literal["asc","desc"]` with the helper in `app/api/v1/domains/entities/endpoints/categories.py`, `entity_types.py` and `sources.py`; remove the now-unused `.lower()` branch. Behavior preserved (FR-011): existing `tests/domains/test_categories.py`, `test_entity_types.py`, `test_sources.py` and `tests/test_cache_reference_reads.py` stay green (note: the tie-breaker is the only new effect)
- [X] T005 Extend `CRUDBaseService._build_query` in `app/api/common/services/base_service.py` with optional `sort`/`order` (default: current `order_by(id)`), implemented with `apply_sort`; pass them through `get_multi` and `get_all`. Add a test in `tests/test_sorting.py` that the default stays id-ordered

## Phase 3: User Story 1 — Countries (P1) — commit `fix(countries): validate sort/order and drop the dead relations param`

**Independent test**: `GET /countries?sort=__class__`, `order=sideways` each return 422; valid values work; `relations=entities` no longer errors.

- [X] T006 [US1] Write failing tests in `tests/domains/test_countries.py`: 422 for `sort` outside {name,id} and for `order` outside {asc,desc} (including `DESC`), `relations` ignored without error, `sort=name&order=desc` descending, default name asc, `sort=id`
- [X] T007 [US1] In `app/api/v1/domains/countries/endpoints/countries.py` type `sort` as `Literal["name","id"]` and `order` as `SortOrder`; remove the `relations` parameter from list and detail
- [X] T008 [US1] In `app/api/v1/domains/countries/services/country.py` keep the unlimited `get_multi` override (the base one caps at 100) but build its query with `_build_query(sort=, order=)`; delete the Python `sorted(...)` in the endpoint. `tests/domains/test_countries.py` fully green

## Phase 4: User Story 2 — Users and entities ordering (P2) — two commits

**Independent test**: create several rows, request every allowed `sort` in both directions, verify order across pages; invalid values give 422.

### Users — commit `fix(users): validate sort/order and apply ordering`

- [ ] T009 [US2] Write failing tests in `tests/domains/test_users.py`: ordering by each of id/email/full_name asc and desc across two pages with no duplicates/omissions (use `size=2`), rows with null `full_name` always last in both directions, 422 for invalid `sort`/`order`, default email asc
- [ ] T010 [US2] In `app/api/v1/domains/users/endpoints/users.py` type `sort` as `Annotated[Literal["id","email","full_name"], Query(...)]`, `order` as `SortOrder`, and pass both to `user_service.get_all(...)` (T005). (`User` and `Country` have no `created_at` column, verified 2026-11-25: the old examples advertised it and it silently fell back to `id`; it is not offered, no migration added.)

### Entities — commit `fix(entities): validate sort/order and apply ordering`

- [ ] T011 [US2] Write failing tests in `tests/domains/test_entities.py`: ordering by id/name/created_at asc and desc across pages together with the existing filters, 422 for invalid `sort`/`order`, default name asc
- [ ] T012 [US2] Add `sort`/`order` parameters to `get_paginated` in `app/api/v1/domains/entities/services/entity.py` using `apply_sort`, and type them in `list_entities` (`app/api/v1/domains/entities/endpoints/entities.py`) as `Literal["id","name","created_at"]` and `SortOrder`

## Phase 5: User Story 3 — Compose password (P3) — commit `fix(compose): require POSTGRES_PASSWORD instead of a default`

- [ ] T013 [US3] Add a step to the `build` job in `.github/workflows/ci.yml`: `POSTGRES_PASSWORD= docker compose config` must fail and its output contain "POSTGRES_PASSWORD is required" (the step fails if compose succeeds); a second command with `POSTGRES_PASSWORD=x` must succeed. Run both locally first and confirm the first one fails today (red) before T014
- [ ] T014 [US3] In `docker-compose.yml` (db service, line ~35) replace `${POSTGRES_PASSWORD:-myths}` with `${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required: set it in .env (see .env.example)}`; check no other service or file relies on the default (`pgadmin`, `myths` script, CI)
- [ ] T015 [US3] Update the README variable table (line ~108): `POSTGRES_PASSWORD` required, no default

## Phase 6: Polish — commit `docs(roadmap): close session 1.4`

- [ ] T016 Full verification: `./myths test` (coverage gate 68%), `uvx black --check app`, run quickstart.md steps 3 and 5 by hand
- [ ] T017 Update `docs/ROADMAP.md`: mark 1.4 done with a summary (items 1, 3, 4 were already resolved; helper `sorting.py`; users/entities ordering was ignored before) and add the detected debt (`datetime.utcnow()` in utils.py/health.py/entity.py, `.dict()` in api_responses.py, `Optional[X]` style, `python-jose` maintenance). Update the "Estado al" line
- [ ] T018 Push, PR against `develop`, wait for green CI, `gh pr merge --admin --merge --delete-branch`, confirm CI on develop, close #54 by hand with evidence per item, then write the prompt for session 1.5 (DELETE /entities/{id}/relations/{relation_id})

## Dependencies

T001 → Phase 2 (T002→T003→T004,T005) → US1 (needs T005) and US2 (needs T005) → US3 is independent of Phases 2-4 (can run any time after T001) → Polish.

**Parallel**: US3 (T013–T015) touches only compose/README/one test file and can be done independently of US1/US2; the other stories share `sorting.py` and `base_service.py`, so run them in order.

## Implementation strategy

MVP = Phase 2 + US1 (the only item where hostile input can currently cause a 500). Then US2, then US3. Stop and report if any existing test in categories/entity-types/sources changes behavior in T004.

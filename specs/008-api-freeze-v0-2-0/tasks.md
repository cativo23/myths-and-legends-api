# Tasks: API freeze for v0.2.0

**Input**: `specs/008-api-freeze-v0-2-0/` (plan.md, spec.md, research.md, data-model.md, contracts/api-changes.md, quickstart.md)

**Tests**: Required (constitution I, Test-First). Every story starts with tests that are run and seen failing for the right reason (Red) before any code.

**Rules for all tasks**: sync `def`, `HTTPException` envelope, do not run `black` on `tests/`, one commit per story (US1 has two), conventional commits. Run tests with `./myths test <path> --no-cov`; the stack must be up (`./myths up -d`).

## Format: `- [ ] [ID] [P?] [Story] Description with file path`

## Phase 1: Setup

- [ ] T001 Confirm a clean baseline: `./myths up -d`, then `./myths test` is green (expected 454 passed, coverage gate holds); note the numbers in the PR description
- [ ] T002 Commit the spec artifacts in `specs/008-api-freeze-v0-2-0/` as `docs(spec): add spec, plan and tasks for the v0.2.0 freeze`

## Phase 2: Foundational

None. Stories touch different files and are independent, except US4 and US5 which close after US1 to US3.

## Phase 3: User Story 1 - One predictable rate-limit response (P1)

**Goal**: every 429 has `{"detail": {"message", "type": "rate_limit_exceeded", "retry_after"}}` (spec FR-001, FR-002; research R1, R2).
**Independent test**: `./myths test tests/e2e/test_rate_limit_boundaries.py tests/domains/test_auth.py --no-cov`

- [ ] T003 [US1] Red: in `tests/e2e/test_rate_limit_boundaries.py` replace `_assert_429_with_json_body` and the "default limit" NOTE with one `_assert_429_envelope` helper asserting the exact keys `message`, `type`, `retry_after` and no top-level `error`; apply it to all five tests (refresh and logout hit the default limit). Run and confirm the two default-limit tests fail on the `{"error": ...}` body
- [ ] T004 [US1] Green: in `app/api/common/middleware/rate_limiter.py` change `rate_limit_exception_handler` from `async def` to `def`, with a one-line comment that slowapi's middleware replaces coroutine handlers with its own `{"error"}` one (research R1). Run T003 tests: green
- [ ] T005 [US1] Commit `fix(rate-limit): return one 429 body for every limit`
- [ ] T006 [US1] Red: add a test (same file) that `retry_after` is a positive integer not greater than 60 for both a per-route and a default 429; confirm it fails because it is `None`
- [ ] T007 [US1] Green: in `rate_limiter.py` compute `retry_after` from the limiter's window stats of `exc.limit` (seconds until reset, at least 1), `None` if it cannot be read. Run the rate-limit tests: green
- [ ] T008 [US1] Commit `feat(rate-limit): report seconds until the window resets in retry_after`

## Phase 4: User Story 2 - Each relation appears once (P1)

**Goal**: one summary per symmetric pair in `GET /entities/{id}` and `GET /entities/{id}/relations` (FR-003 to FR-005, FR-012; research R3).
**Independent test**: `./myths test tests/e2e tests/domains/test_entities.py --no-cov` (relation tests live in `test_entities.py`)

- [ ] T009 [US2] Find every test that pins two rows for a symmetric pair: `grep -rn -i "symmetric\|two rows\|SIBLINGS" tests` (known: `tests/e2e/conftest.py` `graph_snapshot`, `tests/e2e/test_entity_graph_journey.py`, `tests/domains/test_entities.py`); list them in the commit message body
- [ ] T010 [US2] Red: update those tests to the new expectation (a symmetric relation once from each end, `direction` = `origin`; directed relations unchanged; deleting from either end removes it from both). Add unit-level tests for: one stored row only (legacy) still shows once; mixed symmetric and directed counts distinct relationships. Run and confirm they fail on duplicates
- [ ] T011 [US2] Green: add one summary builder to `app/api/v1/domains/entities/services/entity_relation.py` that turns the entity's relation rows into `EntityRelationSummary` items, deduplicating symmetric types by `(relation_type, related_entity_id)` and preferring the row where the queried entity is origin (see data-model.md Entity relation table). Replace the two copied loops in `app/api/v1/domains/entities/endpoints/entities.py` (`get_entity`, `get_entity_relations`) with it
- [ ] T012 [US2] Run `./myths test tests/e2e tests/domains --no-cov`: green
- [ ] T013 [US2] Commit `fix(entities): list each symmetric relation once`

## Phase 5: User Story 3 - Credit the artist (P1)

**Goal**: optional `image_credit` on create, update and read (FR-006 to FR-008; research R4).
**Independent test**: `./myths test tests/domains/test_entities.py --no-cov` plus the migration check in quickstart.md

- [ ] T014 [US3] Red: in `tests/domains/test_entities.py` add tests: create with credit returns it trimmed (`"  Ana Perez  "` becomes `"Ana Perez"`); create without credit returns `null`; blank becomes `null`; over 255 characters returns 422; update omitting it keeps it; update with `""` clears it; list and detail both return it. Confirm they fail (field missing)
- [ ] T015 [US3] Add `image_credit` to the `Entity` model in `app/api/v1/domains/entities/models/entity.py` per data-model.md `Entity.image_credit`
- [ ] T016 [US3] Add `image_credit` to `EntityBase` (with the trim and blank-to-`None` validator), `EntityUpdate`, and the read schemas in `app/api/v1/domains/entities/schemas/entity.py` per data-model.md `Entity.image_credit`; pass it in the field-by-field response built in `get_entity` in `endpoints/entities.py`
- [ ] T017 [US3] Create the Alembic revision `./myths alembic revision --autogenerate -m "add entity image credit"` and review it: only `add_column`/`drop_column` per data-model.md `Entity.image_credit`, down revision `b0ac58dc2755`, working `downgrade`
- [ ] T018 [US3] Verify on PostgreSQL: `./myths alembic upgrade head`, `downgrade -1`, `upgrade head`, then `./myths psql -c "\d entity"` shows `image_credit | character varying(255)` nullable (constitution V); record the output in the PR description
- [ ] T019 [US3] Run `./myths test tests/domains --no-cov`: green
- [ ] T020 [US3] Commit `feat(entities): add optional image credit`

## Phase 6: User Story 4 - Typed dates and truthful docs (P2)

**Goal**: typed, aware-UTC `expires_at`; Salvadoran docs; Fair Use (FR-009 to FR-011; research R5, R6).
**Independent test**: `./myths test tests/domains/test_auth.py tests/test_openapi_catalog.py --no-cov`

- [ ] T021 [US4] Red: in `tests/domains/test_auth.py` assert login and refresh `expires_at` parses as an ISO 8601 datetime **with** a UTC offset and is in the future; add a test that the full schema (`app.openapi()`, the one the frontend snapshots) declares `components.schemas.Token.properties.expires_at` as `{"type": "string", "format": "date-time"}`. Confirm both fail
- [ ] T022 [US4] Green: `expires_at: datetime` in `app/api/v1/domains/users/schemas/token.py`; `get_token_expiry` in `app/core/security.py` returns `datetime.fromtimestamp(exp, tz=timezone.utc)`. `grep -rn "get_token_expiry\|utcnow" app tests` for comparisons with naive datetimes and fix them. Run auth tests: green
- [ ] T023 [US4] Commit `fix(auth): type expires_at as an aware UTC datetime`
- [ ] T024 [US4] Red: new `tests/test_openapi_catalog.py` that scans the **full** schema from `app.openapi()` (not the filtered public/admin ones: the frontend consumes the full one) and fails if it contains `Egypt`, `Greek`, `Norse`, `Aztec`, `Japanese`, `Anubis` (case-insensitive), and that `info.description` of that schema contains `Fair Use`. Confirm it fails and prints the offending words
- [ ] T025 [US4] [P] Rewrite examples and descriptions for the real catalog (CHARACTER, PLACE, OBJECT, GROUP, EVENT; MYTH, LEGEND, TRADITION; Salvadoran examples such as El Cipitio, La Siguanaba, El Cadejo) in `app/api/v1/domains/entities/schemas/entity_type.py`, `schemas/entity.py`, `endpoints/entities.py` (type filter), `endpoints/entity_types.py`
- [ ] T026 [US4] [P] Rewrite the description in `app/main.py` for a Salvadoran catalog and add the "Fair Use" section (educational and cultural use, artwork belongs to its credited artists, how to request corrections); do not alter the contact data already there
- [ ] T027 [US4] [P] Update `README.md` (what the catalog is, real types and categories, `image_credit`, one 429 body) and drop foreign-mythology wording
- [ ] T028 [US4] Run the OpenAPI scan and `./myths test tests --no-cov -k "openapi or auth"`: green
- [ ] T029 [US4] Commit `docs(api): describe the Salvadoran catalog and add a Fair Use note`

## Phase 7: User Story 5 - A tagged, documented release (P2)

**Goal**: CHANGELOG, ROADMAP, tag after merge (FR-013, FR-014; research R8).

- [ ] T030 [US5] Move `[Unreleased]` entries in `CHANGELOG.md` under `## [0.2.0]` (date left as the merge date to fill at tag time) and add: 429 unified plus real `retry_after`, one relation per symmetric pair (both endpoints), `image_credit`, typed aware `expires_at`, docs and Fair Use. Mark the contract changes as Changed or Added accordingly
- [ ] T031 [US5] Update `docs/ROADMAP.md`: 1.7 done with the decisions; risks 16 to 19 closed with what was chosen; 2.3 block note changed to "unblocked once the `v0.2.0` tag exists"
- [ ] T032 [US5] Fix the stale line in `CLAUDE.md` ("Image upload is integrated into entity create/update") only if Carlos agrees; otherwise leave it and note it in the PR
- [ ] T033 [US5] Commit `docs: close session 1.7 in changelog and roadmap`

## Phase 8: Polish and delivery

- [ ] T034 Run the full suite: `./myths test` green, coverage not below the gate (SC-006); run `./myths alembic upgrade head` and the quickstart "By hand" checks 1 to 5
- [ ] T035 Review the diff as if someone else wrote it, then dispatch `superpowers:code-reviewer` on the branch diff; fix real findings with a test first
- [ ] T036 Push `feat/api-freeze-v0-2-0`, open the PR against `develop` (title under 70 characters, body: decisions, migration output, test numbers, the two flagged scope items), wait for CI green. If CI does not start, close and reopen
- [ ] T037 **Stop and ask Carlos** before merging; after merge, ask again before creating the tag. Then `git tag -a v0.2.0 <merge-commit>` and `git push origin v0.2.0` (FR-014), fix the CHANGELOG date, and hand off the frontend: replace `openapi/openapi.json` with the **full** schema (`app.openapi()`, same export as in the web repo's `openapi/SOURCE.md`) taken from the tag, `pnpm client:generate`, update `openapi/SOURCE.md`

## Dependencies and order

- Phase 1 first. US1, US2, US3 are independent (US2 and US3 both edit `endpoints/entities.py` and `schemas/entity.py` in different places: do them in order to avoid conflicts, no [P]).
- US4's docs tasks T025 to T027 run after US3 (they touch the same schema file) and are parallel with each other.
- US5 after US1 to US4. Phase 8 last.

## Parallel opportunities

- T025, T026, T027 (different files).
- T006/T007 could overlap with T009 (different modules) if worked by two people; in this single-session flow they run sequentially.

## Implementation strategy

MVP is US1 plus US2 (the two changes the frontend cannot work around). Commit and keep tests green after every story; do not batch. If the review rejects the two flagged scope items (real `retry_after`, dedup on `/relations`), drop T006 to T008 or limit T011 to the detail endpoint without touching other tasks.

## Format validation

All tasks have a checkbox and an ID, user-story tasks carry `[US#]`, and each names a file or command. Constrained field `Entity.image_credit` is cited to `data-model.md` in T015, T016 and T017.

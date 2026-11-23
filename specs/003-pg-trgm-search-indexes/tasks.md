---
description: "Task list for trigram search indexes (pg_trgm)"
---

# Tasks: Substring search acceleration with trigram indexes

**Input**: Design documents from `/specs/003-pg-trgm-search-indexes/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (no contracts: no API change)

**Tests**: REQUIRED (constitution Principle I) for what SQLite can observe: the model-metadata guard is committed red first. GIN usage and the migration round trip cannot run in the SQLite suite; they are verified by hand on PostgreSQL 15 (quickstart.md, Constitution V) and the evidence goes in the PR body.

**Organization**: One commit per concern (guard test, model, migration, docs). The index list, names and ordering are defined in [data-model.md](data-model.md) and are not repeated here. This feature adds no constrained fields (no column, type or nullability change), so no field citations are needed.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (baseline)

- [ ] T001 Run `./myths test --no-cov` on the untouched branch and record the green baseline (329 passed expected); run `uvx black --check app`
- [ ] T002 Confirm the stack is up and `myths` is at head: `./myths alembic current` shows `ce04f762989d`; capture the baseline schema with `pg_dump -s` (filter `grep -v -E '^\\(un)?restrict'`) into the scratchpad for quickstart step 5

---

## Phase 2: Foundational (blocks every story)

**Purpose**: the model edit and the migration that all four stories depend on.

### Tests (write first, see them fail)

- [ ] T003 Create `tests/domains/test_trigram_search_indexes.py` using only model metadata (no DB fixture needed). Two behaviors, one test each: (a) `should_not_declare_a_btree_index_on_entity_description`: no index in `Entity.__table__.indexes` covers only the `description` column; (b) `should_not_declare_trigram_indexes_on_models`: no index in `Entity.__table__.indexes` or `Location.__table__.indexes` has a name ending in `_trgm` (they live only in the migration because SQLite `create_all` cannot build them; the docstring says why)
- [ ] T004 Run the file and confirm test (a) fails for the right reason (`ix_entity_description` is still declared via `index=True`) and test (b) passes. Commit as `test(entities): add guard tests for trigram index declarations`

### Implementation

- [ ] T005 Remove `index=True` from `Entity.description` in `app/api/v1/domains/entities/models/entity.py` (one-line comment: description is served by a trigram index created in the migration; see research.md Decision 3). Run T003's file until green. Commit as `refactor(entities): drop btree index on entity.description from model`
- [ ] T006 Create `alembic/versions/<rev>_add_trigram_search_indexes.py` with `./myths alembic revision -m "add trigram search indexes"` (hand-written body, not autogenerate; confirm `down_revision = 'ce04f762989d'`). The `api` container runs as root, so the generated file is root-owned: fix it right away with `sudo chown "$USER":"$USER"` on that file (or `ls -l` first to confirm). `upgrade`: `op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")`, then the four GIN `gin_trgm_ops` indexes, then drop `ix_entity_description` (order in data-model.md). `downgrade`: recreate `ix_entity_description` as in `bd728d1bc3f7`, then drop the four GIN indexes, leaving the extension installed. Comments: why GIN only here (SQLite), why the extension is not dropped, why defaults for `fastupdate`
- [ ] T007 Run `./myths alembic upgrade head` on the dev DB; confirm the indexes (quickstart step 6) and that `ix_entity_name` and `ix_location_department` are still present (FR-004). Commit as `feat(db): add pg_trgm and trigram indexes for substring search`

**Checkpoint**: schema in place; stories below are verification of behavior.

---

## Phase 3: User Story 1 - Entity search stays fast (Priority: P1)

**Goal**: entity search uses the three entity trigram indexes together, with identical results.

**Independent Test**: quickstart steps 9 (entity query), 10 and 11.

- [ ] T008 [US1] Forced plan on the seed data (quickstart step 9): `BitmapOr` over `ix_entity_name_trgm`, `ix_entity_description_trgm`, `ix_entity_origin_trgm`; save the plan text for the PR
- [ ] T009 [US1] Natural plan on a throwaway database `trgm_scratch` with ~80k synthetic entities (quickstart step 10): record plan type and times for a 3+ character term matching under 5% of rows (targets: under 10 ms; baseline 224 ms); also record a 2-character term (documented table-scan fallback). Drop `trgm_scratch` afterwards and confirm it is gone
- [ ] T010 [US1] Result parity (quickstart step 11): same rows with and without index access for several terms, including mixed case and an entity with NULL `description`/`origin`

---

## Phase 4: User Story 2 - Location department filter stays fast (Priority: P1)

**Goal**: the department filter uses `ix_location_department_trgm`, with identical results.

**Independent Test**: quickstart steps 9 (location query) and 10.

- [ ] T011 [P] [US2] Forced plan on the seed data for `SELECT count(*) FROM location WHERE department ILIKE '%san%'`: `Bitmap Index Scan` on `ix_location_department_trgm`
- [ ] T012 [US2] In `trgm_scratch` (same session as T009, with ~100k synthetic locations) record the natural plan and time for the count and the unpaginated lookup (target: under 10 ms after the SC-002 correction; baseline ~30 ms); note that `ORDER BY id LIMIT` paging does not change (research.md)

---

## Phase 5: User Story 3 - Upgrade and revert safely (Priority: P1)

**Goal**: up → down → up works on real PostgreSQL and leaves the schema as specified.

**Independent Test**: quickstart steps 4, 5, 7 and 8.

- [ ] T013 [US3] Privilege check (quickstart step 4): `pg_available_extension_versions.trusted = t` for `pg_trgm`; record that the dev role is a superuser so the non-superuser path is documented, not exercised (spec assumption)
- [ ] T014 [US3] `./myths alembic downgrade -1`: four `*_trgm` gone, `ix_entity_description` back as B-tree, row counts unchanged, `pg_trgm` still installed; `pg_dump -s` equals the T002 baseline apart from the extension lines
- [ ] T015 [US3] `./myths alembic upgrade head` again (extension already present, no error); confirm head and the same index set as T007 (including the kept B-tree indexes); leave the dev DB at head

---

## Phase 6: User Story 4 - API behavior unchanged (Priority: P2)

**Goal**: no observable API change; suite green with no test modified.

**Independent Test**: quickstart steps 2, 3 and 12.

- [ ] T016 [US4] `./myths test` (full, with coverage gate): all green, at least 329 passed plus the new guard tests, no pre-existing test modified (`git diff develop -- tests` shows only the new file)
- [ ] T017 [P] [US4] `uvx black --check app`
- [ ] T018 [US4] API smoke (quickstart step 12): `/api/v1/entities/search?q=god` and `/api/v1/locations/?department=San` return 200 with the same items as before

---

## Phase 7: Polish & cross-cutting

- [ ] T019 Update `docs/ROADMAP.md`: mark session 1.2 closed with the evidence summary; link to `specs/003-pg-trgm-search-indexes/research.md` for the documented limitations (FR-009: terms under 3 chars, unescaped wildcards, no accent folding, write cost); record follow-ups (composite `ix_location_department` in migrated DBs vs single-column in the model; terms under 3 chars and unescaped wildcards as possible future work) and keep the existing pending items. Commit as `docs(roadmap): close session 1.2 and record follow-ups`
- [ ] T020 Self-review the full diff as if written by someone else (comments explain why, one concern per commit); mark all tasks `[X]`; commit as `docs(specs): mark self-review done for trigram indexes`

---

## Dependencies & Execution Order

- T001 → T002 → T003 → T004 → T005 → T006 → T007 (strict order: Red, then Green, then migration).
- US1 (T008-T010), US2 (T011-T012) and US3 (T013-T015) all need T007. T014 and T015 change the schema, so run T008, T011 and T013 (and T009/T012 on the scratch database) before T014, or re-run T015 afterwards. Suggested order: T013, T008, T011, T009, T012, T010, T014, T015.
- US4 (T016-T018) after T015, so the suite and smoke run against the final state.
- T019 and T020 last.

## Parallel Opportunities

- T011 and T017 are independent of the other tasks in their phases ([P]).
- T009/T012 (scratch database) can run while T016 (full suite, ~3 min) runs; they touch different databases.

## Implementation Strategy

MVP is Phase 2 plus US1: the migration with the three entity indexes already delivers the issue's goal; US2 to US4 are verification and regression guards. Do not skip US3 (Constitution V).

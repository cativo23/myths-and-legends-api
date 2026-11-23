---
description: "Task list for database-level CHECK constraints on enum columns"
---

# Tasks: Database-level constraints on enum columns

**Input**: Design documents from `/specs/002-enum-check-constraints/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (no contracts: no API change)

**Tests**: REQUIRED (constitution Principle I). Rejection tests are committed red first, then the models turn them green; the migration sync test is written before the migration.

**Organization**: Grouped by user story. One commit per concern (tests, models, migration, docs). Allowed values per column are defined in [data-model.md](data-model.md) and are not repeated here.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (baseline)

- [X] T001 Run `./myths test --no-cov` on the untouched branch and record the green baseline (276 passed expected), confirming nothing in `tests/` builds these models from raw strings (`grep -rnE "(Category|EntityType|Characteristic|EntityRelation|Source)\(" tests`)

---

## Phase 2: Foundational

None. No dependency, config or schema change blocks the stories.

---

## Phase 3: User Story 1 - The database rejects invalid enum values (Priority: P1)

**Goal**: all five columns refuse out-of-set writes at the database layer, in the test DB and in real schemas.

**Independent Test**: `./myths test tests/domains/test_enum_check_constraints.py --no-cov` is green.

### Tests (write first, see them fail)

- [X] T002 [US1] Create `tests/domains/test_enum_check_constraints.py` using the existing `db` fixture. Parametrize over the five columns cited in data-model.md: `Category.name`, `EntityType.name`, `Characteristic.type`, `EntityRelation.relation_type`, `Source.source_type`. Cases: (a) every allowed value read from the enum is accepted; (b) each invalid value (`"INVALID"`, lowercase of a valid value, trailing space, `""`) raises `sqlalchemy.exc.IntegrityError` on execute, **parametrized per (column, invalid value)** so every case gets its own `db` fixture and a failed statement cannot contaminate the next; (c) updating a valid row to an invalid value raises `IntegrityError`; (d) inserting NULL raises `IntegrityError` (existing NOT NULL, not the new constraint; guards the spec edge case). Child tables need a parent `Entity` (and a second one for `EntityRelation`) built with `Category`/`EntityType` members. Insert invalid values with `sqlalchemy.insert()` on the table or `session.execute(text(...))`, not via the enum, to mimic raw SQL
- [X] T003 [US1] Run the new file and confirm it fails for the right reason: the invalid-value cases *do not raise* (no constraint yet). Commit as `test(entities): add failing tests for enum CHECK constraints`

### Implementation

- [X] T004 [US1] Add `enum_check(column, enum_cls, name)` to `app/api/v1/domains/entities/enums.py`, returning a `sqlalchemy.CheckConstraint` of the form `column IN ('A', 'B', ...)` built from the enum values, with a one-line comment on why values come from the enum (prevents drift, see research.md R3)
- [X] T005 [P] [US1] Add `enum_check("name", CategoryName, "ck_category_name")` to `__table_args__` in `app/api/v1/domains/entities/models/category.py` (`Category.name`, data-model.md)
- [X] T006 [P] [US1] Add `enum_check("name", EntityTypeName, "ck_entity_type_name")` to `__table_args__` in `app/api/v1/domains/entities/models/entity_type.py` (`EntityType.name`, data-model.md)
- [X] T007 [P] [US1] Append `enum_check("type", CharacteristicType, "ck_characteristic_type")` to the existing `__table_args__` in `app/api/v1/domains/entities/models/characteristic.py` (`Characteristic.type`, data-model.md)
- [X] T008 [P] [US1] Append `enum_check("relation_type", RelationType, "ck_entity_relation_relation_type")` to the existing `__table_args__` in `app/api/v1/domains/entities/models/entity_relation.py` (`EntityRelation.relation_type`, data-model.md)
- [X] T009 [P] [US1] Append `enum_check("source_type", SourceType, "ck_source_source_type")` to the existing `__table_args__` in `app/api/v1/domains/entities/models/source.py` (`Source.source_type`, data-model.md)
- [X] T010 [US1] Run `./myths test tests/domains/test_enum_check_constraints.py --no-cov` until green, then commit as `feat(entities): declare CHECK constraints on enum columns` (the helper and the five models are one concern)

**Checkpoint**: US1 complete in the test DB; real databases still need the migration (US2).

---

## Phase 4: User Story 2 - Existing databases upgrade safely (Priority: P1)

**Goal**: one migration adds the five constraints, aborts cleanly on dirty data, and reverts exactly.

**Independent Test**: quickstart.md steps 3 to 7 pass on PostgreSQL 15.

### Tests (write first)

- [ ] T011 [US2] Add to `tests/domains/test_enum_check_constraints.py` a sync test that loads the migration module by path (`importlib.util.spec_from_file_location` on `alembic/versions/*_add_enum_check_constraints.py`) and asserts its frozen `CHECKS` values equal the five enums and its constraint names equal the names on the models' `__table_args__` (research.md R5). Confirm it fails because the migration does not exist yet

### Implementation

- [ ] T012 [US2] Create the migration with `./myths alembic revision -m "add enum check constraints"` (hand-written, not autogenerate: Alembic does not compare CHECK constraints), `down_revision = '0f2ce4cae13f'`. Define a module-level `CHECKS` list of `(table, column, constraint_name, allowed_values)` hardcoded from data-model.md for all five columns (`Category.name`, `EntityType.name`, `Characteristic.type`, `EntityRelation.relation_type`, `Source.source_type`)
- [ ] T013 [US2] Implement `upgrade()` in that migration: for each entry build the query with `sa.table()` / `sa.column()` constructs (`select(col).distinct().where(col.not_in(allowed))`, no identifier interpolation into raw SQL) and run it via `op.get_bind()`; collect offenders across all five columns and raise one `RuntimeError` naming table, column and values (no data changes); only if none, call `op.create_check_constraint` for each
- [ ] T014 [US2] Implement `downgrade()`: `op.drop_constraint(name, table, type_='check')` for the five constraints, in reverse order
- [ ] T015 [US2] Run T011's sync test green and commit as `feat(db): add migration for enum CHECK constraints`
- [ ] T016 [US2] Execute quickstart.md steps 3 to 7 against the dev PostgreSQL 15 (clean upgrade, direct invalid insert rejected per column, down, up again with identical `pg_dump -s`/constraint listing, abort on one deliberately dirty row then cleanup). Record the observed outputs (constraint listing, the abort message, final `alembic current`) in the PR description; leave the dev DB at head with no invalid rows

**Checkpoint**: migration verified up → down → up on real PostgreSQL (constitution V).

---

## Phase 5: User Story 3 - API behavior is unchanged (Priority: P2)

**Goal**: zero regressions for API clients.

**Independent Test**: full suite green with no pre-existing test modified.

- [ ] T017 [US3] Run `./myths test` (full suite with coverage): expect all green, coverage at or above the 68% gate; confirm `git diff --stat -- tests/` shows only additions to the new file
- [ ] T018 [US3] Execute quickstart.md step 8 (`GET /api/v1/categories`, `GET /api/v1/entity-types` return 200 with seeded values)

---

## Phase 6: Polish & Cross-Cutting

- [ ] T019 Update `docs/ROADMAP.md`: mark session 1.1 done (feature `specs/002-enum-check-constraints/`, #68 to close by hand), refresh the status date, and record follow-ups: `./myths psql` targets nonexistent service `pgsql` (should be `db`); enum edits now require a migration (sync test guards it). Add an `[Unreleased]` CHANGELOG entry in `CHANGELOG.md`. Commit as `docs(roadmap): close session 1.1 and record follow-ups`
- [ ] T020 Self-review the full diff as if written by someone else (constitution workflow): naming, WHY comments, no stray files, `docs/superpowers/plans/` not included
- [ ] T021 Push `feature/enum-check-constraints`, open a PR against `develop` (title under 70 chars, imperative), wait for green CI, merge with `gh pr merge --admin --merge`, confirm develop's post-merge CI is green, delete the branch, close #68 by hand after verifying against the code

---

## Dependencies & Execution Order

- T001 → T002 → T003 (red) → T004 → T005–T009 (parallel, different files) → T010 (green).
- US2 depends on US1 (models define the names the sync test compares): T011 → T012 → T013 → T014 → T015 → T016.
- US3 runs after US2 (T017/T018 validate the final state). Polish last.
- Commit order mirrors concerns: tests (T003), models (T010), migration (T015), docs (T019).

## Parallel Example

T005–T009 touch five independent model files and can be done together once T004 exists.

## Implementation Strategy

MVP is US1 (constraints enforced in models and tests), but it must not merge without US2: models declaring constraints that no real database has would break the schema/model parity. Ship all three stories in one PR.

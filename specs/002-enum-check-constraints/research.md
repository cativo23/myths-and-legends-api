# Research: enum CHECK constraints

## R1. CHECK vs native PostgreSQL ENUM
- **Decision**: `CHECK (col IN (...))`.
- **Rationale**: decided by the maintainer and the roadmap. Changing a vocabulary later is
  drop-and-recreate one constraint in a migration; native `ALTER TYPE ... ADD VALUE` has
  transaction restrictions and cannot remove values. CHECK also works unchanged on SQLite, which is
  what the test suite runs on, so the model-level constraint is exercised by every test.
- **Alternatives**: native ENUM (rejected: harder to evolve, not enforced in SQLite tests).

## R2. Where constraints are declared
- **Decision**: on the models via `__table_args__`, with explicit names
  `ck_category_name`, `ck_entity_type_name`, `ck_characteristic_type`,
  `ck_entity_relation_relation_type`, `ck_source_source_type`.
- **Rationale**: `create_all` then enforces them in the test DB; metadata has no
  `naming_convention`, so an unnamed CHECK would get a backend-generated name and could not be
  dropped deterministically. All names are < 63 chars.
- **Alternatives**: migration-only constraints (rejected: tests would not exercise them, and models
  would drift from the real schema).
- **Note**: Alembic autogenerate does not compare CHECK constraints, so declaring them on the models
  creates no autogenerate noise.

## R3. Building the `IN` clause
- **Decision**: a small helper in `enums.py`, `enum_check(column, enum_cls, name)`, returning a
  `CheckConstraint` whose text is `column IN ('A', 'B', ...)` built from the enum values.
- **Rationale**: five call sites; deriving values from the enum prevents model/enum drift and
  avoids hand-quoting errors. Enum values are developer-controlled constants, not user input, so
  there is no injection surface.
- **Alternatives**: five hand-written strings (rejected: drift risk is the very problem the issue
  describes, and tests would need to re-derive them anyway).

## R4. Migration pre-check and abort
- **Decision**: in `upgrade()`, for each `(table, column, constraint, allowed)` run
  `SELECT DISTINCT col FROM table WHERE col NOT IN (:allowed...)` with bound parameters; if any
  rows, collect all offenders across the five columns and raise one `RuntimeError` naming
  table, column and values. Only then create the constraints.
- **Rationale**: Postgres `ADD CONSTRAINT` would also fail on violations but with a generic message
  naming only the constraint; the pre-check gives an actionable message. Reporting all columns in
  one pass avoids fix-one-rerun-repeat. DDL is transactional on Postgres, so an abort leaves
  nothing behind; no data is modified.
- **Alternatives**: `NOT VALID` (rejected by the maintainer: leaves a half-enforced constraint);
  auto-repair/delete (rejected: silently destroys reference data).

## R5. Migration values are frozen
- **Decision**: the migration hardcodes the allowed values in a module-level `CHECKS` structure.
- **Rationale**: a migration is history; importing the live enums would change what an old
  revision does when the enum changes. A test loads the migration module and asserts `CHECKS`
  equals the current enums, so a future enum edit without a new migration fails the suite
  (covers the spec's sync edge case).
- **Alternatives**: import enums in the migration (rejected as above).

## R6. Test strategy
- **Decision**: parametrized pytest cases on the existing SQLite `db` fixture: for each of the five
  columns, an invalid value (and `''`, wrong case) raises `IntegrityError`, every allowed value is
  accepted, and an update to an invalid value is rejected. Parent rows (entity) are built with
  existing fixtures/helpers for child tables.
- **Rationale**: SQLite enforces CHECK by default, and the models now declare them. The existing
  suite already uses enum members only, so SC-005 holds (verified by grep of direct model
  construction in `tests/`).
- **Limits (documented, accepted)**: SQLite does not prove the Postgres DDL; that is covered by the
  manual up → down → up on PG 15 (FR-009), including an invalid-row abort check.
- **Alternatives**: Postgres-backed pytest (rejected by the maintainer: new infra, out of scope).

## R7. Verification environment
- Dev DB inspected 2026-11-23: all values valid (3 categories, 5 entity types, 4 characteristic
  types, 2 relation types, 4 source types; 8 entities). Alembic head `0f2ce4cae13f`.
- `./myths psql` is broken (targets service `pgsql`; the service is `db`). Not fixed here (out of
  scope); quickstart uses `docker compose exec -T db psql` with the container's own env vars.

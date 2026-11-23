# Implementation Plan: Database-level constraints on enum columns

**Branch**: `feature/enum-check-constraints` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-enum-check-constraints/spec.md`

## Summary

Add one named `CHECK (col IN (...))` constraint to each of the five enum-like `String(50)` columns.
The constraints are declared on the models (so `Base.metadata.create_all`, used by the SQLite test
database, enforces them) and shipped to existing databases by one Alembic migration. The migration
first scans each column for out-of-set values and aborts with a clear message without touching data;
its `downgrade` drops exactly the five constraints. Rejection is proven by parametrized
`IntegrityError` tests on the existing `db` fixture; up → down → up is verified manually on
PostgreSQL 15 (see [quickstart.md](quickstart.md)).

## Technical Context

**Language/Version**: Python 3.10 (Docker), CI matrix 3.10 / 3.11 / 3.12

**Primary Dependencies**: SQLAlchemy 2.0 (`CheckConstraint`), Alembic; no new dependencies

**Storage**: PostgreSQL 15 (runtime), SQLite (test suite, via `create_all`)

**Testing**: pytest via `./myths test`; new file `tests/domains/test_enum_check_constraints.py`

**Target Platform**: Linux container

**Project Type**: web-service (FastAPI)

**Performance Goals**: N/A (CHECK on an `IN` list of ≤6 literals; negligible write cost)

**Constraints**: constraint names ≤ 63 chars (Postgres identifier limit); no `naming_convention` in
metadata so names are explicit; migration must be transactional (Postgres DDL is) so an abort leaves
the schema unchanged

**Scale/Scope**: 5 models, 1 migration, 1 test file, 1 tiny helper

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Test-First | PASS | Rejection tests written first and seen failing (no constraint yet → insert of an invalid value succeeds, test fails for the right reason); then constraints added. Sync test (migration sets == enums) also written first |
| II. Security-First | PASS | Strengthens DB-level guarantees; no secrets; migration error message exposes only table/column/offending enum value, shown to the maintainer running Alembic, not to API clients |
| III. Minimalism | PASS | No native ENUM, no backfill/repair logic, no CI infra, no Postgres test in pytest. One small helper builds the `IN` clause from an enum so the model cannot drift from the enum |
| IV. Layered / sync | PASS | No endpoint, service or schema change; only model `__table_args__` |
| V. Migrations | PASS | Working `downgrade`; verified up → down → up on real PostgreSQL 15; Pydantic validation now backed by DB constraints |

No violations; Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-enum-check-constraints/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
└── tasks.md             # created by /speckit-tasks
```

(No `contracts/`: no API surface changes.)

### Source Code (repository root)

```text
app/api/v1/domains/entities/
├── enums.py                         # + enum_check() helper
└── models/
    ├── category.py                  # + CheckConstraint in __table_args__
    ├── entity_type.py               # idem
    ├── characteristic.py            # idem (extends existing __table_args__)
    ├── entity_relation.py           # idem (extends existing __table_args__)
    └── source.py                    # idem (extends existing __table_args__)
alembic/versions/<rev>_add_enum_check_constraints.py   # down_revision = 0f2ce4cae13f
tests/domains/test_enum_check_constraints.py
docs/ROADMAP.md                      # close session 1.1, record follow-ups
CHANGELOG.md                         # [Unreleased] entry
```

**Structure Decision**: follow the existing domain layout; the migration is a frozen snapshot with
the allowed values hardcoded (never imported from the app, so later enum edits cannot rewrite
history).

## Complexity Tracking

Not applicable.

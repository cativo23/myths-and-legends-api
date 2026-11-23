# Implementation Plan: Substring search acceleration with trigram indexes

**Branch**: `feature/pg-trgm-search-indexes` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-pg-trgm-search-indexes/spec.md`

## Summary

One Alembic migration enables `pg_trgm` (`CREATE EXTENSION IF NOT EXISTS`), creates four GIN
`gin_trgm_ops` indexes (`entity.name`, `entity.description`, `entity.origin`, `location.department`)
and drops the ordinary B-tree `ix_entity_description`. The model drops `index=True` on
`Entity.description` so `create_all` (SQLite test DB) does not recreate it; the GIN indexes live only
in the migration because SQLite cannot build them. No query, endpoint or schema changes. The only
automated test is a model-metadata guard (Red first: the B-tree is still declared); index usage and
up → down → up are verified by hand on PostgreSQL 15 per [quickstart.md](quickstart.md), as the suite
cannot exercise Postgres-only features (Constitution V).

## Technical Context

**Language/Version**: Python 3.10 (Docker), CI matrix 3.10 / 3.11 / 3.12

**Primary Dependencies**: Alembic, SQLAlchemy 2.0 (`op.create_index(..., postgresql_using='gin', postgresql_ops=...)`); no new Python dependencies

**Storage**: PostgreSQL 15 (`postgres:15-alpine`, `pg_trgm` 1.6 bundled, trusted); SQLite for the test suite

**Testing**: pytest via `./myths test`; one new metadata test; manual EXPLAIN and migration round trip on real Postgres

**Target Platform**: Linux container

**Project Type**: web-service (FastAPI)

**Performance Goals**: entity search for a selective term under 10 ms at ~80k rows (baseline 224 ms); department filter under 5 ms at ~100k rows (baseline ~30 ms)

**Constraints**: index names ≤ 63 chars; `gin_trgm_ops` is Postgres-only so the indexes cannot be declared on models; term shorter than 3 chars falls back to a table scan (accepted); migration must be transactional

**Scale/Scope**: 1 migration, 1 model line, 1 test, docs (ROADMAP)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Test-First | PASS | Metadata guard test written first and seen failing (`ix_entity_description` still declared). The Postgres behavior cannot be tested in the SQLite suite; it is verified manually and recorded in the PR (see Complexity Tracking) |
| II. Security-First | PASS | No new input, no secrets, no new privileges: `pg_trgm` is trusted, so the DB owner suffices; queries unchanged and parameterized |
| III. Minimalism | PASS | No query rewrite, no `min_length`, no wildcard escaping, no index tuning, no full-text search. Four indexes, each justified by measurement |
| IV. Layered / sync | PASS | No endpoint, service or schema change; one model attribute edited |
| V. Migrations | PASS | Working `downgrade`; verified up → down → up on PostgreSQL 15; EXPLAIN evidence for index use |

## Project Structure

### Documentation (this feature)

```text
specs/003-pg-trgm-search-indexes/
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
app/api/v1/domains/entities/models/entity.py        # Entity.description: drop index=True
alembic/versions/<rev>_add_trigram_search_indexes.py  # down_revision = ce04f762989d
tests/domains/test_trigram_search_indexes.py        # metadata guard
docs/ROADMAP.md                                     # close 1.2, record follow-ups
```

**Structure Decision**: existing domain layout; no new modules.

## Complexity Tracking

| Deviation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Behavior not covered by an automated test (GIN usage, extension) | The suite runs on SQLite via `create_all`; trigram operators do not exist there | A Postgres service in pytest/CI is new infrastructure and out of scope for this session (Constitution III); manual EXPLAIN + round trip is the Constitution V requirement |

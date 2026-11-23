# Research: trigram search indexes

All figures: single run, PostgreSQL 15, throwaway database, synthetic data (80k entities with Zipf
vocabulary, 5% NULL description, 25% NULL origin; 100k locations over 33 departments). Order of
magnitude, not a benchmark.

## Decision 1: Which columns to index

**Decision**: GIN `gin_trgm_ops` on `entity.name`, `entity.description`, `entity.origin`,
`location.department`.

**Rationale**: `EntityService.search()` is an `OR` of three `ILIKE '%term%'`. The planner can only
use an index for an `OR` if every branch has one: with only `description` indexed the plan stayed a
Seq Scan (233 ms vs 224 ms); with all three it became a `BitmapOr` of three bitmap index scans
(3-5 ms). `Location.department` is filtered by the same pattern (count and unpaginated lookup:
~30 ms → ~2 ms).

**Alternatives considered**:
- Only `description` (the roadmap's literal wording): the index would never be used.
- Full-text search (`tsvector`): matches whole words only, changes results, needs a query change; rejected by the roadmap ("no query change").
- Skip `department`: leaves the same root cause open on a second table; the GIN index is also smaller (2.3 MB) than the existing B-tree (3.1 MB).

## Decision 2: Keep `ix_entity_name` and `ix_location_department`

**Decision**: keep both; drop only `ix_entity_description`.

**Rationale**: they still serve equality, `ORDER BY`, and the composite `ix_entity_active (is_active, name)`; dropping them widens scope. Chosen by Carlos in this session.

**Finding (out of scope)**: the dev database's `ix_location_department` is composite `(department, municipality)`, but the model declares single-column indexes (`index=True`), so migrated databases and `create_all` databases already differ. Not touched here; noted in the ROADMAP follow-ups.

## Decision 3: Indexes only in the migration

**Decision**: do not declare the GIN indexes in `__table_args__`.

**Rationale**: `create_all` also builds model-declared indexes on SQLite, where `gin_trgm_ops` does not exist; it would break the whole suite. `Entity.description` loses `index=True` so the dropped B-tree is not recreated.

**Alternatives considered**: `postgresql_using`/`postgresql_ops` on the model with a dialect guard: extra machinery for no behavior gain.

## Decision 4: Extension handling and privileges

**Decision**: `op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")` in `upgrade`; the downgrade leaves it installed (clarified).

**Rationale**: the dev role is a superuser, and in PG13+ `pg_trgm` is *trusted* (`pg_available_extension_versions.trusted = t`), so a non-superuser DB owner with CREATE on the database can install it. Leaving it on downgrade keeps up → down → up idempotent.

**Evidence**: dev DB owner `myths`; `pg_available_extensions` lists `pg_trgm` 1.6, not installed before this change.

## Decision 5: GIN options

**Decision**: defaults (`fastupdate=on`).

**Rationale**: `fastupdate=off` made 10k-row inserts ~6x slower (1.4 s → 8.7 s). `gin_pending_list_limit` (4 MB) needs no tuning at this write volume.

## Measured trade-offs (accepted)

| Item | Without | With |
|---|---|---|
| Insert 10k entities | 84 ms | 1.4 s (all three entity GIN) |
| Update 3k entities | ~35 ms | 450-475 ms |
| Index size at 80k entities | n/a | description 42 MB, origin 10 MB, name 4.1 MB; heap is 56 MB |
| Term of 2 chars | Seq Scan 220 ms | index cannot help; forcing it 550 ms |

`description` is the costly one (~10x insert cost); it is required for the OR to use any index.

## Edge-case checks

- NULL `description`/`origin`: `ILIKE` on NULL is NULL, so no match before or after; GIN skips NULLs; results unchanged.
- Case: `ILIKE` already case-insensitive; trigram index gives the same rows (`FOPESO` = `fopeso`, 48 rows).
- Wildcards `%`/`_` in the term are not escaped today; unchanged.
- Collation `en_US.utf8` worked without issue.
- Only `ILIKE` call sites in `app/`: `entity.py:109-111`, `locations.py:47`, `location.py:19`. Nothing else searches by pattern (alternative_names, countries, sources, categories untouched).

## How to prove index use on small tables

With 8 entities the planner prefers a Seq Scan even when the index exists. Two options:

1. Forced, inside a transaction: `BEGIN; SET LOCAL enable_seqscan=off; EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) <query>; ROLLBACK;` after `ANALYZE`.
2. Natural: throwaway database with ~80k synthetic entities and a term of 3+ characters matching under 5% of rows.

Procedure details in [quickstart.md](quickstart.md).

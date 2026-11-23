# Feature Specification: Substring search acceleration with trigram indexes

**Feature Branch**: `feature/pg-trgm-search-indexes` (spec directory is independent of branch name)

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "Search with pg_trgm (issue #60, roadmap 1.2). Enable the trigram extension and add trigram GIN indexes on entity.name, entity.description, entity.origin and location.department so the existing substring searches (case-insensitive `%term%`) stop scanning whole tables. Drop the useless B-tree ix_entity_description (model and migration). Keep ix_entity_name and ix_location_department. No query change, no API behavior change. One migration with a working downgrade, verified up → down → up on real PostgreSQL, plus EXPLAIN evidence that the planner uses the new indexes."

## Clarifications

### Session 2026-11-23

- Q: Should the downgrade uninstall the trigram extension or leave it installed? → A: Leave it installed; the downgrade only drops the four trigram indexes and restores `ix_entity_description`. Schema comparison after the round trip ignores the extension.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity search stays fast as the catalog grows (Priority: P1)

A client calls the entity search with a term. The system matches the term anywhere inside an entity's name, description or origin, ignoring case. Today every search reads the whole entity table; with the new indexes, a selective term is answered from the indexes.

**Why this priority**: This is the point of issue #60. The search is the one public read path that cannot be served by ordinary indexes, and it gets slower linearly with catalog size.

**Independent Test**: On a PostgreSQL database with about 80,000 synthetic entities, run the search query for a selective term and confirm the query plan combines index lookups on all three columns instead of reading the whole table, and that the elapsed time drops by an order of magnitude (measured baseline: ~224 ms before, ~3-5 ms after).

**Acceptance Scenarios**:

1. **Given** the indexes exist and the table is large enough for the planner to prefer them, **When** the search runs for a term of 3 or more characters that matches a small share of rows, **Then** the plan uses the name, description and origin indexes together and no sequential scan of the entity table.
2. **Given** the indexes exist, **When** the search runs for any term, **Then** the set of entities returned is identical to what it was before the indexes (same rows, same matching rules).
3. **Given** an entity whose description or origin is empty (NULL), **When** a search runs, **Then** that entity still matches through its name, and is never matched through the empty column.

---

### User Story 2 - Location filter by department stays fast (Priority: P1)

A client lists locations filtered by department using a partial, case-insensitive match. The filter is answered from an index instead of reading the whole location table.

**Why this priority**: Same root cause as Story 1 on a second table; the roadmap and issue #60 explicitly bundle it.

**Independent Test**: On PostgreSQL with about 100,000 synthetic locations, run the department filter used for the count and for the unpaginated lookup, and confirm the plan uses the department index (measured baseline: ~30 ms before, ~2 ms after).

**Acceptance Scenarios**:

1. **Given** the indexes exist and the table is large enough, **When** locations are filtered by a partial department name of 3 or more characters, **Then** the plan uses the department index.
2. **Given** the indexes exist, **When** the filter runs, **Then** the locations returned are identical to before.

---

### User Story 3 - Existing databases upgrade and revert safely (Priority: P1)

A maintainer upgrades a database that already holds data, and can revert the upgrade. The upgrade needs no elevated database privileges beyond what the application's own database owner has, and never alters row data.

**Why this priority**: Schema changes cannot be trivially rolled back in production (Constitution V).

**Independent Test**: Against a real PostgreSQL instance with seed data, run upgrade, downgrade, upgrade; compare the schema before and after the round trip.

**Acceptance Scenarios**:

1. **Given** a database at the previous revision, **When** the upgrade runs, **Then** the four new indexes exist, the old ordinary description index is gone, and the existing name and department indexes are still present.
2. **Given** the upgrade has been applied, **When** it is reverted, **Then** the four new indexes are removed, the old ordinary description index is restored, and the schema matches the pre-upgrade schema (ignoring the random lines pg_dump emits and the trigram extension, which stays installed).
3. **Given** the upgrade ran on a database where the extension is already installed, **When** it runs again or after a revert, **Then** it does not fail on the existing extension.
4. **Given** the revert has run, **When** the database is inspected, **Then** no row data changed.

---

### User Story 4 - API behavior is unchanged (Priority: P2)

API clients see no difference: same endpoints, same results, same responses.

**Why this priority**: Regression guard; the change is meant to be invisible except for speed.

**Independent Test**: The existing test suite passes with no test changed, including on the SQLite-based test database, which must not be asked to create trigram indexes.

**Acceptance Scenarios**:

1. **Given** the change is applied, **When** the full existing test suite runs, **Then** it passes with no test modified.

---

### Edge Cases

- A term of fewer than 3 characters cannot use the trigram indexes; the planner reads the table, and forcing the index is slower (measured ~550 ms vs ~220 ms). No validation is added; this is documented.
- A term containing `%` or `_` acts as a wildcard because the term is not escaped today. Behavior is unchanged and out of scope; a term made only of wildcards still reads the whole table.
- Accents are not unified, exactly as today.
- On tiny tables (such as the 8-entity seed) the planner prefers reading the table even with the indexes present; verification therefore forces index use inside a rolled-back transaction or uses a larger synthetic data set.
- NULL description or origin: rows with NULL never match that column and are not indexed there; results do not change.
- Write cost grows: the three entity indexes raise bulk insert time (measured: 10,000 rows from ~84 ms to ~1.4 s) and updates, and add roughly 56 MB at 80,000 entities. Accepted trade-off, documented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The database MUST have trigram substring-matching support enabled by the upgrade, and the upgrade MUST NOT fail if it is already enabled.
- **FR-002**: The system MUST provide a trigram index on each of: entity name, entity description, entity origin, and location department, named `ix_entity_name_trgm`, `ix_entity_description_trgm`, `ix_entity_origin_trgm`, `ix_location_department_trgm`.
- **FR-003**: The ordinary index `ix_entity_description` MUST be removed both from migrated databases and from the entity model declaration, so a fresh table built from the model does not recreate it.
- **FR-004**: The ordinary indexes `ix_entity_name` and `ix_location_department` MUST remain.
- **FR-005**: Entity search and the location department filter MUST keep their current query text and matching semantics (case-insensitive substring, same rows returned).
- **FR-006**: The upgrade MUST have a downgrade that removes the four trigram indexes, restores `ix_entity_description` as it was, and leaves row data untouched. The extension is left installed on downgrade (decided in clarification), so up → down → up never fails on it and nothing else that might use it breaks.
- **FR-007**: The trigram indexes MUST be created only by the migration, not declared on the models, so the SQLite-based test database does not attempt to create them.
- **FR-008**: The migration MUST be verified up → down → up on real PostgreSQL, and index usage MUST be demonstrated with query plans for the entity search (index lookups on all three columns combined) and the department filter, following a documented procedure that works on small tables.
- **FR-009**: The feature documentation MUST record the limitations: terms under 3 characters, unescaped wildcards, no accent folding, and the write-cost and size trade-off.
- **FR-010**: The upgrade MUST work with the privileges of the application's own database owner (no superuser requirement).

### Key Entities *(include if feature involves data)*

- **Entity**: a mythological entity; its name, description and origin are searched by substring. Description and origin may be empty.
- **Location**: a place tied to an entity; its department is filtered by substring.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With about 80,000 entities, a search for a term matching under 2% of rows returns in under 10 ms (baseline ~224 ms), and its plan reads no whole-table scan.
- **SC-002**: With about 100,000 locations, filtering by a partial department name returns in under 5 ms for the count and unpaginated lookup (baseline ~30 ms).
- **SC-003**: The same search and filter inputs return exactly the same results before and after, and the existing test suite passes unchanged.
- **SC-004**: The upgrade, downgrade and re-upgrade complete without error on a real PostgreSQL instance, and the schema after downgrade matches the schema before upgrade (the extension stays installed).
- **SC-005**: The four trigram indexes exist after upgrade and `ix_entity_description` (ordinary) does not; after downgrade the reverse holds.

## Assumptions

- Measured figures come from a single run on synthetic data (Zipf-like vocabulary, 5% NULL descriptions, 25% NULL origins) and are order-of-magnitude evidence, not a benchmark; the success thresholds above leave headroom.
- The application's database role owns its database, and the trigram extension is classified as trusted in PostgreSQL 15, so no superuser is needed. The development role is a superuser, so this is confirmed by the documented privilege check, not exercised.
- Index options stay at defaults (including deferred-write buffering); tuning them was measured as worse for inserts.
- The department filter with `ORDER BY id LIMIT` paging already finishes quickly through the primary key and is not expected to improve; the gain is on the count and unpaginated lookup.
- Adding a minimum term length, escaping wildcard characters, accent folding, and full-text search are out of scope.
- The roadmap constraint "no query change, only indexes" is kept.
- Trigram indexes cannot be tested on the SQLite test database; they are verified by hand against real PostgreSQL (Constitution V).

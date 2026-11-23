# Feature Specification: Database-level constraints on enum columns

**Feature Branch**: `feature/enum-check-constraints` (spec directory is independent of branch name)

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "Add DB-level CHECK constraints to the five enum-like columns (Category.name, EntityType.name, Characteristic.type, EntityRelation.relation_type, Source.source_type) so raw SQL, manual fixes or bulk imports cannot store values outside the allowed sets. Closes #68. CHECK (not native ENUM); declared on the models with explicit names; one migration with a working downgrade that aborts with a clear message, without touching data, if existing rows violate the sets; verified up → down → up on real PostgreSQL. No change to the enums or to API behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The database rejects invalid enum values (Priority: P1)

A maintainer or script writes directly to the database (SQL, admin tool, import). Any attempt to store a value outside the allowed set in one of the five columns is refused by the database itself, regardless of the API layer.

**Why this priority**: This is the whole point of the issue: today the API validator is the only guard, so any non-API write path can corrupt reference data silently.

**Independent Test**: For each of the five columns, insert a row with an out-of-set value directly through the data layer and confirm it is rejected; insert each allowed value and confirm it is accepted.

**Acceptance Scenarios**:

1. **Given** the constraints are in place, **When** a row is inserted with a value outside the allowed set in any of the five columns, **Then** the write is rejected with an integrity error and nothing is stored.
2. **Given** the constraints are in place, **When** a row is inserted or updated with any allowed value, **Then** the write succeeds.
3. **Given** an existing valid row, **When** it is updated to an out-of-set value, **Then** the update is rejected and the row keeps its old value.

---

### User Story 2 - Existing databases upgrade safely (Priority: P1)

A maintainer upgrades a database that already holds data. If every value is valid the upgrade completes; if any row violates a set, the upgrade stops before changing anything and says which table, column and values are the problem.

**Why this priority**: Migrations cannot be trivially rolled back in production; silently fixing or deleting reference data would be worse than refusing.

**Independent Test**: Run the upgrade on a clean seeded database (succeeds) and on a database with one deliberately invalid row (aborts, message names table, column and value, data and schema unchanged).

**Acceptance Scenarios**:

1. **Given** a database whose values are all valid, **When** the upgrade runs, **Then** it completes and the five constraints exist.
2. **Given** a database with an out-of-set value in any of the five columns, **When** the upgrade runs, **Then** it aborts with a message naming the table, column and offending values, and no data or schema change persists.
3. **Given** the upgrade has been applied, **When** it is reverted, **Then** the constraints are removed and data is untouched; re-applying it succeeds (up → down → up).

---

### User Story 3 - API behavior is unchanged (Priority: P2)

API clients see no difference: the same values are accepted and rejected, with the same responses, as before.

**Why this priority**: The constraints mirror existing validation, so this is a regression guard rather than new value.

**Independent Test**: The existing test suite passes unmodified.

**Acceptance Scenarios**:

1. **Given** the constraints are in place, **When** the full existing test suite runs, **Then** it passes with no test changed.

---

### Edge Cases

- A value differing only in case or whitespace (e.g. `myth`, `MYTH `) is outside the set and is rejected.
- An empty string is rejected.
- NULL on these columns stays governed by the existing NOT NULL rule; the constraints do not change nullability.
- Seeded data (all current values) satisfies the constraints.
- The allowed sets in the constraints must stay in sync with the Python enums; a future enum change needs a new migration (out of scope here, documented in the assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The database MUST reject any value outside the allowed set for `Category.name` (MYTH, LEGEND, TRADITION).
- **FR-002**: The database MUST reject any value outside the allowed set for `EntityType.name` (CHARACTER, PLACE, OBJECT, GROUP, EVENT).
- **FR-003**: The database MUST reject any value outside the allowed set for `Characteristic.type` (PHYSICAL, APPEARANCE, ABILITY, WEAKNESS).
- **FR-004**: The database MUST reject any value outside the allowed set for `EntityRelation.relation_type` (MOTHER_CHILD, FATHER_CHILD, SIBLINGS, GUARDIAN_PLACE, ENEMIES, ALLIES).
- **FR-005**: The database MUST reject any value outside the allowed set for `Source.source_type` (BOOK, ORAL_TRADITION, WEB, DOCUMENT).
- **FR-006**: Each constraint MUST have an explicit, stable name, and MUST be declared on the data models so that schemas created from the models (including the test database) enforce it identically.
- **FR-007**: A single schema migration MUST add the five constraints and provide a working revert that removes exactly those constraints.
- **FR-008**: Before adding constraints, the migration MUST check each column for out-of-set values and, if any exist, abort with a message naming table, column and offending values; it MUST NOT modify or delete data.
- **FR-009**: The migration MUST be verified up → down → up against a real PostgreSQL instance, and the procedure documented in the feature's quickstart.
- **FR-010**: Tests MUST prove at the database layer (not only request validation) that each of the five columns rejects an invalid value and accepts every allowed value.
- **FR-011**: The allowed sets, the API-level enums and API behavior MUST NOT change.

### Key Entities

- **Category / EntityType**: reference tables whose `name` identifies a fixed vocabulary.
- **Characteristic / Source / EntityRelation**: per-entity records whose `type`, `source_type` and `relation_type` classify them within a fixed vocabulary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 5 of 5 columns refuse an out-of-set write made directly against the database.
- **SC-002**: 100% of the allowed values (22 across the five columns) are still accepted.
- **SC-003**: The upgrade on a database containing one invalid row changes nothing and reports the offending table, column and value in a single message.
- **SC-004**: The up → down → up cycle completes with no errors on real PostgreSQL, and the schema after the second "up" is identical to the one after the first.
- **SC-005**: The existing test suite passes with zero modified tests and coverage stays above the project gate.

## Assumptions

- Mechanism chosen by the maintainer: CHECK constraints (not native enum types), so changing a vocabulary later is one constraint swap in a new migration.
- Adding or renaming an enum value later requires a new migration updating the constraint; keeping Python enums and constraints in sync is a maintainer responsibility, covered by tests that read the values from the enums.
- The development database was inspected: all existing values are valid, so the upgrade succeeds there.
- Migration verification runs manually against PostgreSQL 15 (local compose stack); the automated suite keeps using its current test database and no CI change is made.
- Out of scope: changing the enums, API behavior, native database enum types, CI changes.

# Feature Specification: Delete an entity relation

**Feature Branch**: `feature/delete-entity-relation` (spec directory is independent of branch name)

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "Decide and implement `DELETE /entities/{id}/relations/{relation_id}` (roadmap 1.5)."

## Investigation (2026-11-25)

- Relations can only be listed and created (`GET`/`POST /entities/{id}/relations`). There is no way to correct a wrong relation short of deleting the whole entity (which cascades to its relations).
- Symmetric types (SIBLINGS, ALLIES, ENEMIES) are stored as **two rows** (forward and reverse, different ids); `POST` returns only the forward id. `GET` lists both rows, each with its own id and a direction.
- Non-symmetric types (MOTHER_CHILD, FATHER_CHILD, GUARDIAN_PLACE) are a single row.
- Every other `DELETE` in the API is superuser-only, returns 204 without body and 404 when the target is missing. Authorization is resolved before the lookup, so non-superusers never learn whether a target exists. No delete is audited today.

## Clarifications

### Session 2026-11-25 (Carlos)

- Q: Implement or discard? → A: Implement.
- Q: What does deleting a symmetric relation remove? → A: Both rows, atomically; non-symmetric types remove only their row.
- Q: Which relations can be deleted through `/entities/{id}/...`? → A: Any relation where that entity is origin or destination (same set `GET` lists). Otherwise 404 "Relation not found", with the same message whether the relation does not exist or does not involve that entity.
- Q: Response and audit? → A: 204 No Content. No new audit log; existing request logging is kept. A cross-cutting audit of write endpoints is recorded as a future roadmap item.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove a wrong relation (Priority: P1)

A superuser who loaded a wrong relation between two entities removes it, using the relation id shown in the entity's relations list, without touching the entities themselves.

**Why this priority**: It is the whole feature; today the mistake is uncorrectable.

**Independent Test**: Create a relation, delete it, then list the entity's relations and confirm it is gone while both entities remain.

**Acceptance Scenarios**:

1. **Given** a non-symmetric relation (e.g. MOTHER_CHILD) from A to B, **When** a superuser deletes it via A's path, **Then** the response is 204 and the relation no longer appears for A or B.
2. **Given** a symmetric relation (e.g. SIBLINGS) between A and B (two rows), **When** a superuser deletes either row's id via either entity's path, **Then** the response is 204 and neither A nor B lists the relation anymore.
3. **Given** a relation where B is the destination, **When** a superuser deletes it via B's path using the id B's list shows, **Then** it is deleted.
4. **Given** a symmetric relation A-B and a different relation type between the same pair, **When** the symmetric one is deleted, **Then** the other relation is untouched.

---

### User Story 2 - Clear errors and no information leak (Priority: P1)

Invalid targets and unauthorized callers get predictable errors that do not reveal what exists.

**Why this priority**: Security-first principle; destructive endpoint.

**Independent Test**: Call with missing/foreign ids and without superuser rights and check status codes and messages.

**Acceptance Scenarios**:

1. **Given** no token, **When** the endpoint is called, **Then** 401. **Given** a non-superuser token, **Then** 403, regardless of whether the entity or relation exists.
2. **Given** a superuser and a nonexistent entity id, **Then** 404 "Entity not found".
3. **Given** a superuser, an existing entity, and a relation id that does not exist **or** does not involve that entity, **Then** 404 "Relation not found" (identical in both cases), and nothing is deleted.
4. **Given** an id of 0 or negative, **Then** 422.

### Edge Cases

- Deleting a symmetric relation whose reverse row is already missing (legacy data): the existing row is still deleted and the call succeeds.
- Deleting the same relation twice: second call is 404 "Relation not found".
- Failure while deleting one of the two rows must leave both rows in place (atomic).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let a superuser delete a relation by id through the entity's relations path.
- **FR-002**: The system MUST accept any relation where the path entity is origin or destination.
- **FR-003**: For SIBLINGS, ALLIES and ENEMIES the system MUST delete the relation and its reverse row in a single atomic operation; for other types it MUST delete only the addressed row.
- **FR-004**: The system MUST reject unauthenticated callers (401) and non-superusers (403) before checking existence of any target.
- **FR-005**: The system MUST answer 404 "Entity not found" for a missing entity and 404 "Relation not found" when the relation is missing or does not involve that entity, never deleting anything in those cases.
- **FR-006**: The system MUST reject non-positive ids with 422.
- **FR-007**: On success the system MUST respond 204 with no body and leave the entities and all other relations unchanged.
- **FR-008**: The list of symmetric relation types MUST have a single definition shared by creation and deletion.
- **FR-009**: The endpoint documentation MUST list the 204, 401, 403, 404 and 422 responses.

### Key Entities

- **Entity relation**: a typed, directed link between two entities, identified by its own id; symmetric types exist as a forward/reverse pair.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A superuser can correct a wrong relation in one request, with 0 side effects on entities or other relations.
- **SC-002**: After deleting a symmetric relation, 100% of the pair's listings stop showing it (no one-sided leftovers).
- **SC-003**: Non-superusers get the same response (401/403) for existing and non-existing targets.
- **SC-004**: Every error path (missing entity, missing relation, foreign relation, invalid id) is covered by an automated test.

## Assumptions

- No schema change or migration is needed: relations already cascade on entity deletion.
- Updating (PUT/PATCH) a relation is out of scope; delete-then-create covers corrections.
- No new audit logging (future cross-cutting item: who/what for all write endpoints).
- Existing authorization rules (superuser-only writes) apply unchanged.

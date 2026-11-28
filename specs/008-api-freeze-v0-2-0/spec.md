# Feature Specification: API freeze for v0.2.0

**Feature Branch**: `feat/api-freeze-v0-2-0` (spec directory is independent of branch name)

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "Roadmap 1.7: close the API contract for the frontend. Resolve risks 16 (two 429 bodies), 17 (duplicated symmetric relations), 18 (artist credit, outdated docs) and 19 (untyped `Token.expires_at`); add a Fair Use note to `/docs`, update the CHANGELOG and roadmap, and tag `v0.2.0` after merge."

## Investigation (2026-11-27)

- The per-route limit (login, recover, reset) answers `{"detail": {"message", "type": "rate_limit_exceeded", "retry_after"}}`. The default limit is enforced by `SlowAPIMiddleware`, which bypasses the custom handler and answers `{"error": "Rate limit exceeded: ..."}`. Both are pinned as current behavior by the E2E tests of spec 007.
- `GET /entities/{id}` lists both stored rows of a symmetric relation (siblings, allies, enemies), so each end sees the relation twice. Spec 006 and the E2E tests document this as current behavior. Storage, `POST` and `DELETE` of relations are not part of this change.
- An entity stores only `image_url`; there is nowhere to record who made the artwork. The frontend design brief requires crediting the Salvadoran artists.
- The OpenAPI descriptions and examples of entity types, the entity filter and the entity schema still speak of Egyptian, Greek, Norse, Aztec and Japanese mythologies. The README does not say the catalog is Salvadoran. Real types are CHARACTER, PLACE, OBJECT, GROUP, EVENT; real categories are MYTH, LEGEND, TRADITION.
- `Token.expires_at` is declared with no type, so generated clients see an unknown value and the format is not in the contract.
- There is no "Fair Use" note in `/docs` and `v0.2.0` does not exist yet (only `v0.1.0`).

## Clarifications

### Session 2026-11-27 (Carlos)

- Q: How is the 429 unified? → A: Both limits answer the existing `detail` envelope with `message`, `type` and `retry_after`; the frontend already reads `detail.retry_after`.
- Q: How are duplicated symmetric relations fixed? → A: The entity detail shows one relation per symmetric pair, seen from the queried entity. Storage is unchanged.
- Q: Where does the artist credit live? → A: An optional credit field on the entity (new nullable column plus migration), accepted on create and update and returned on read.
- Q: How is the work delivered? → A: One branch, one PR to `develop`, atomic commits per risk. The tag is created only after merge and with Carlos's explicit confirmation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One predictable rate-limit response (Priority: P1)

A client (the web frontend) that is throttled needs to tell the user how long to wait, without caring which limit was hit.

**Why this priority**: The frontend carries no adapters; a second error shape would force one or break the retry message.

**Independent Test**: Trigger the default limit on any route and the per-route limit on login; compare the bodies.

**Acceptance Scenarios**:

1. **Given** a client over the per-route limit, **When** it calls a limited route, **Then** it receives 429 with a `detail` object holding `message`, `type` = `rate_limit_exceeded` and `retry_after`.
2. **Given** a client over the default limit, **When** it calls any other route, **Then** it receives 429 with exactly the same body shape.
3. **Given** a throttled response of either kind, **Then** the `Retry-After` information is available in the same field in both.

---

### User Story 2 - Each relation appears once (Priority: P1)

A reader of an entity sees its relations as the catalog means them: one line per relationship.

**Why this priority**: The catalog detail page groups and links relations; duplicates would show "siblings: X, X".

**Independent Test**: Create a symmetric relation and read both ends; each shows one relation.

**Acceptance Scenarios**:

1. **Given** a symmetric relation (siblings, allies or enemies) between A and B, **When** A's detail is read, **Then** it lists the relation once, pointing to B; **When** B's detail is read, **Then** it lists it once, pointing to A.
2. **Given** a directed relation (mother-child, father-child, guardian-place), **When** either end is read, **Then** it appears once with the correct direction, as today.
3. **Given** a symmetric relation deleted from either end, **Then** it disappears from both details, as today.
4. **Given** an entity with symmetric and directed relations, **Then** the total number listed equals the number of distinct relationships.

---

### User Story 3 - Credit the artist of an entity's artwork (Priority: P1)

An administrator records who made an entity's image, and readers see the credit next to it.

**Why this priority**: The artworks come from Salvadoran artists and the design brief requires crediting them; without a place to store it, the catalog cannot comply.

**Independent Test**: Create an entity with a credit, read it back; create one without a credit and confirm it still works.

**Acceptance Scenarios**:

1. **Given** a superuser, **When** they create or update an entity with an image credit, **Then** the credit is stored and returned by list and detail.
2. **Given** existing entities, **When** the migration is applied, **Then** they keep working with no credit (empty value).
3. **Given** a credit that is empty, blank or too long, **Then** it is normalized or rejected with the standard validation error.

---

### User Story 4 - Dates a client can parse and docs that describe the real catalog (Priority: P2)

A client developer reads `/docs`, the README and the generated schema and finds an accurate description of a Salvadoran myths and legends catalog.

**Why this priority**: The frontend client and its documentation are generated from this schema; wrong examples propagate downstream.

**Independent Test**: Inspect the OpenAPI document: `expires_at` is a date-time and no example mentions foreign mythologies.

**Acceptance Scenarios**:

1. **Given** the login or refresh response schema, **Then** `expires_at` is declared as a date-time and the value returned is an ISO 8601 timestamp.
2. **Given** the OpenAPI document and README, **Then** descriptions and examples refer to Salvadoran myths and legends and to the real types and categories, and no Egyptian, Greek, Norse, Aztec or Japanese example remains.
3. **Given** `/docs`, **Then** it shows a Fair Use note.

---

### User Story 5 - A tagged, documented release (Priority: P2)

The frontend can pin a stable API version.

**Why this priority**: Roadmap 2.3 reads the OpenAPI of the tag; it is blocked until the tag exists.

**Independent Test**: After merge, the tag `v0.2.0` exists and the CHANGELOG has a matching section.

**Acceptance Scenarios**:

1. **Given** the PR is merged to `develop`, **When** Carlos confirms, **Then** `v0.2.0` is created on the merge commit.
2. **Given** the CHANGELOG, **Then** the new section lists each contract change (429 body, one relation per pair, image credit, typed `expires_at`) and the docs corrections.
3. **Given** the roadmap, **Then** 1.7 is marked done and risks 16 to 19 are closed with the decision taken.

### Edge Cases

- A symmetric relation where only one stored row exists (for example created by hand or legacy data): it must still appear once.
- Entity related to itself: already rejected on create; the detail must not break if legacy data has it.
- Credit given without an image: accepted (it is metadata, not a dependency).
- Update that omits the credit: the stored credit is kept (updates are partial); sending an explicit empty value clears it.
- A throttled response on a route that also fails validation: the 429 wins as today.
- `expires_at` for tokens issued before the change: tokens are short-lived, so no migration of issued tokens is needed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every 429 response, from any limit, MUST have the body `{"detail": {"message", "type": "rate_limit_exceeded", "retry_after"}}`.
- **FR-002**: The 429 body shape MUST be covered by tests for both the default and the per-route limit.
- **FR-003**: The entity detail MUST list each symmetric relation once, from the queried entity's point of view.
- **FR-004**: Directed relations MUST keep their current listing and direction.
- **FR-005**: The stored relation rows, relation creation and relation deletion MUST NOT change.
- **FR-006**: An entity MUST accept an optional image credit on create and update, and MUST return it on list and detail.
- **FR-007**: The image credit MUST be optional, bounded in length and normalized (surrounding whitespace removed, blank treated as absent).
- **FR-008**: The database change MUST be a reversible migration that leaves existing rows valid.
- **FR-009**: `expires_at` in the login and refresh responses MUST be declared as a date-time in the OpenAPI document and returned in ISO 8601.
- **FR-010**: OpenAPI descriptions and examples and the README MUST describe a Salvadoran myths and legends catalog with the real types and categories, with no foreign-mythology examples.
- **FR-011**: `/docs` MUST include a "Fair Use" note.
- **FR-012**: The E2E tests of spec 007 that pin the old 429 body and the duplicated relations MUST be updated to the new behavior.
- **FR-013**: The CHANGELOG and the roadmap MUST record the contract changes and close risks 16 to 19.
- **FR-014**: The tag `v0.2.0` MUST be created only after the PR is merged and Carlos confirms.

### Key Entities

- **Entity**: gains an optional image credit next to its image reference.
- **Entity relation**: unchanged in storage; symmetric ones are presented once per pair in reads.
- **Rate-limit error**: one shape for every throttled response.
- **Token response**: `expires_at` becomes a typed timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of throttled responses, from either limit, share one body shape (verified by tests on both limits).
- **SC-002**: For every symmetric pair, each end lists exactly 1 relation; for entities with N distinct relationships the detail lists N.
- **SC-003**: An entity can be created, updated and read with and without an image credit, and all pre-existing entities remain readable after the migration, in both directions (upgrade and downgrade).
- **SC-004**: A client generated from the OpenAPI document sees `expires_at` as a timestamp, and a search of the OpenAPI document and README finds 0 foreign-mythology examples.
- **SC-005**: The frontend can regenerate its client from the `v0.2.0` tag with no adapter for 429 bodies or relations.
- **SC-006**: The full test suite passes and coverage does not fall below the project gate.

## Assumptions

- The frontend is the only known consumer, and it is still unreleased, so these contract changes are made before the freeze rather than versioned.
- A single `image_credit` text value is enough (artist name); links and licenses are out of scope.
- Public reads stay public and writes stay superuser-gated; the new field follows the same rules.
- Out of scope: new endpoints, relation storage changes, rate-limit values, and frontend changes.
- The Fair Use note is informational text in the API documentation, not a legal review.

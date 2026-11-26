# Feature Specification: End-to-end user-flow tests

**Feature Branch**: `test/e2e-user-flows` (spec directory is independent of branch name)

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "E2E tests (issue #31, roadmap 1.6): entity + relations journey, auth journey with refresh, and rate-limit boundaries."

## Investigation (2026-11-25)

- Single steps are already covered one by one: login, refresh rotation, reuse of a rotated refresh token, logout revoking the refresh token, 429 on login, 429 on the default limit (categories), and the full create/list/delete behavior of entity relations.
- Not covered anywhere: a complete multi-step journey in one flow; "one session per user" (a second login invalidates the first session's refresh token); 429 on password recovery, password reset, refresh and logout.
- Issue #31 predates the current API. Its register flow has no endpoint, and country CRUD, locations and sources already have endpoint-level tests. Its "separate test database" criterion is met by the existing per-test isolated database.

## Clarifications

### Session 2026-11-25 (Carlos)

- Q: Where do the tests run? → A: In-process against the app with the existing test database fixtures (no live stack, no Postgres).
- Q: Where do they live and how are they run? → A: Own `tests/e2e/` directory with a registered `e2e` marker so they can be run alone; they still run in CI and count toward coverage.
- Q: Scope of #31? → A: Only the three flows of roadmap 1.6; obsolete #31 criteria are noted when closing the issue.
- Q: Which rate limits? → A: Password recovery and reset (strict limit) and refresh and logout (default limit). Login and the default limit on a read endpoint are already covered and are not repeated.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entity and relations journey (Priority: P1)

A superuser builds a small mythology graph from scratch and verifies, at each step, what any reader of the API sees.

**Why this priority**: It is the core business flow of the API and the only one that chains reference data, entities and relations.

**Independent Test**: Run the journey alone; it passes only if every step's result is visible in the next step's reads.

**Acceptance Scenarios**:

1. **Given** an authenticated superuser, **When** they create a category, an entity type and several entities, **Then** each is retrievable and the entities reference the created category and type.
2. **Given** those entities, **When** a symmetric relation (siblings, allies or enemies) is created between two of them, **Then** both entities list the relation, each from its own side.
3. **Given** those entities, **When** a directed relation (mother-child, father-child or guardian-place) is created, **Then** only the origin and destination lists show it, once each, with the right direction.
4. **Given** an entity with several relations, **When** its details are requested, **Then** the relation graph shown matches exactly the relations created.
5. **Given** that graph, **When** a symmetric relation is deleted, **Then** it disappears from both entities' details while other relations and the entities remain; **When** a directed relation is deleted, **Then** only that one disappears.
6. **Given** a regular (non-superuser) user at any write step of the journey, **Then** the write is refused and the graph is unchanged.

---

### User Story 2 - Authentication session journey (Priority: P1)

A user logs in and keeps a session alive through token refreshes until logout, and the system enforces one active session per user.

**Why this priority**: A session-security flaw affects every protected endpoint.

**Independent Test**: Run the journey alone; each step depends on the tokens obtained in the previous one.

**Acceptance Scenarios**:

1. **Given** valid credentials, **When** the user logs in, **Then** they receive an access token (usable on a protected endpoint) and a refresh token.
2. **Given** that session, **When** the refresh token is exchanged, **Then** a new working pair is issued and the new access token works.
3. **Given** a refresh token that was already exchanged, **When** it is presented again, **Then** it is rejected, and the session issued by the first exchange keeps working (verified against the current refresh endpoint: a failed reuse does not revoke the newer token).
4. **Given** an active session, **When** the same user logs in again, **Then** the first session's refresh token is rejected and the second session's works (one session per user).
5. **Given** an active session, **When** the user logs out, **Then** the refresh token no longer works.

---

### User Story 3 - Rate-limit boundaries (Priority: P2)

Clients that exceed the allowed request rate on the remaining limited endpoints receive a well-formed 429 response, and one test exceeding a limit never affects another test.

**Why this priority**: Protects brute-force-sensitive endpoints; lower priority because the mechanism is already proven on login and on a read endpoint.

**Independent Test**: For each endpoint, send requests up to its limit, then confirm the next one is rejected.

**Acceptance Scenarios**:

1. **Given** the strict auth limit, **When** password recovery is called one time more than the limit allows, **Then** the extra call returns 429 with a valid JSON error body; same for password reset.
2. **Given** the default limit, **When** refresh is called one time more than the limit allows, **Then** the extra call returns 429; same for logout.
3. **Given** a test module that exhausted limits, **When** any other test module runs right after in the same session, **Then** its first request is not rate-limited (verified by running the rate-limit module followed by another module, not by an order-dependent test).

### Edge Cases

- Requests below the limit must all succeed (the boundary is exact: the last allowed request passes, the next one fails).
- Each rate-limit test exercises a single limited endpoint, so its 429 cannot come from requests to another endpoint (the default limit is shared across endpoints by design).
- Journey steps use fresh data per test, so tests are order-independent and can be run singly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The suite MUST include an entity-and-relations journey covering creation of reference data and entities, symmetric and directed relations, listing, deletion, and verification of the relation graph in the entity details.
- **FR-002**: The suite MUST include an authentication journey covering login, refresh with single-use rotation, rejection of a reused refresh token, logout revoking the refresh token, and one session per user.
- **FR-003**: The suite MUST verify 429 responses on password recovery, password reset, refresh and logout, asserting the exact boundary (last allowed request succeeds, the next is rejected).
- **FR-004**: Each rate-limit test MUST leave no limiter state that affects any other test.
- **FR-005**: E2E tests MUST live in their own directory, carry an `e2e` marker registered in the test configuration, and be runnable on their own through that marker.
- **FR-006**: E2E tests MUST run as part of the normal CI test run and be included in the coverage report, without changes to the coverage gate.
- **FR-007**: E2E tests MUST NOT repeat assertions already made by existing endpoint-level tests; they only assert behavior that arises from chaining steps, plus the gaps listed in the Investigation.
- **FR-008**: E2E tests MUST be deterministic and independent of execution order, using only the project's existing test database isolation.
- **FR-009**: The ROADMAP MUST be updated and issue #31 closed with evidence and a note on which of its criteria are obsolete.

### Key Entities

- **Entity graph**: category, entity type, entities and the typed relations between them (symmetric ones exist as a forward/reverse pair).
- **Session**: the pair of access and refresh tokens of a user; at most one active refresh token per user.
- **Rate-limit budget**: per-client request allowance per minute, with a strict budget on credential-guessing endpoints and a default budget elsewhere.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The three roadmap flows each have at least one automated journey that passes from a clean database and can be run on its own.
- **SC-002**: 100% of the gaps in the Investigation (one session per user; 429 on recover, reset, refresh, logout) are covered by an automated test.
- **SC-003**: The full suite passes in any order and with E2E tests run alone, with no rate-limit interference between tests.
- **SC-004**: The E2E tests run in CI on every pull request without raising the total CI test time by more than 10% over the latest green run on `develop`.
- **SC-005**: Coverage does not fall below the baseline of 85.71% (444 tests before this feature) and stays above the 68% gate.

## Assumptions

- No application code changes are expected; if a journey exposes a defect, work stops and Carlos decides whether to fix it here or log it.
- Existing fixtures (client, database, user and superuser authentication) are reused rather than duplicated.
- The register flow, country CRUD, locations/sources journeys and Postgres-specific behavior are out of scope.
- Rate limits are read from the existing settings, not hardcoded in the tests.

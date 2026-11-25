# Feature Specification: Hardening leftovers of issue #54

**Feature Branch**: `fix/hardening-leftovers-54` (spec directory is independent of branch name)

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "Close the remaining items of issue #54 (roadmap 1.4), verified against the code. Countries list: validated sort/order; the dead `relations` parameter is removed. Users and entities lists: validated sort/order and ordering actually applied. docker-compose: no default database password. Already resolved and out of scope: rate limit on reset-password, limiter docstring, Settings() missing-secrets tests."

## Verification of issue #54 against the code (2026-11-25)

| #54 item | State | Evidence |
|---|---|---|
| 1. Rate limit on `reset-password` | Already resolved | `auth.py` decorates `reset_password` with the auth limit |
| 2. Unbounded free-text params | Open, scope refined below | countries `sort`/`order`/`relations`, users `sort`/`order`, entities `sort`/`order` are plain `str`; categories, entity-types and sources already use `Literal` |
| 3. Rate-limit docstring | Already resolved | `setup_rate_limiter()` states limits are additive |
| 4. Test for `Settings()` without secrets | Already resolved | `tests/test_config.py` covers each missing secret |
| 5. Default `POSTGRES_PASSWORD:-myths` | Open | `docker-compose.yml` db service; README documents `myths` as default |

Additional finding: `GET /users` and `GET /entities` accept `sort`/`order` but never apply them, so the parameters are misleading. `GET /countries` applies `sort` through an unchecked attribute lookup. Its `relations` parameter (list and detail) is dead: `Country` has no relationships (only id, name, status), so any non-empty value ended in a server error (found during implementation, 2026-11-25).

## Clarifications

### Session 2026-11-25

- Q: Users/entities `sort` is accepted but ignored. What to do? → A: Validate with a fixed set of allowed values and make the ordering real.
- Q: How to validate countries `sort`/`order`? → A: Allowed values only (`sort`: name, id; `order`: asc, desc); anything else is rejected with 422.
- Q (during implementation): countries `relations` has no relations to load (the model has none). → A: Remove the parameter from list and detail (Carlos, 2026-11-25).
- Q: Which max length for free params? → A: None needed: with `relations` removed, no free-text query parameter remains on these lists; `sort`/`order` are bounded by their allowed values.
- Q: How must the database container fail without a password? → A: Immediately, with the message "POSTGRES_PASSWORD is required: set it in .env (see .env.example)".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Countries list rejects invalid sort and order values (Priority: P1)

An API client lists countries sorted by a field. Today any `sort` string is looked up as an attribute, so crafted values can produce a server error instead of a clear client error. The `relations` parameter, which can only ever fail, is removed.

**Why this priority**: It is the only item where hostile input currently reaches internals (possible 500), so it is the security-relevant one.

**Independent Test**: Call `GET /countries` with `sort=__class__` and `order=sideways`; each must return 422. Valid values keep working, and `relations=entities` no longer causes an error.

**Acceptance Scenarios**:

1. **Given** countries exist, **When** a client requests `sort=name&order=desc`, **Then** the list comes back ordered by name descending.
2. **Given** any request, **When** `sort` is not one of name, id, **Then** the response is 422.
3. **Given** any request, **When** `order` is not asc or desc, **Then** the response is 422.
4. **Given** a request that still sends `relations`, **When** it is sent, **Then** the parameter is ignored (no error), as it carries no data on countries.

---

### User Story 2 - Users and entities lists honor sort and order (Priority: P2)

An administrator lists users, and any client lists entities, choosing a sort field and direction. Today the values are accepted and silently ignored.

**Why this priority**: Correctness of the public contract; no security impact.

**Independent Test**: Create several users/entities, request each allowed `sort` in both orders, and verify the returned order; request a value outside the allowed set and verify 422.

**Acceptance Scenarios**:

1. **Given** several users, **When** a superuser requests `sort=email&order=desc`, **Then** users are ordered by email descending across pages.
2. **Given** several entities, **When** a client requests `sort=name&order=asc` (the default), **Then** entities are ordered by name ascending.
3. **Given** either list, **When** `sort` or `order` is outside the allowed values, **Then** the response is 422.
4. **Given** no sort/order parameters, **When** a list is requested, **Then** the default ordering (users: email asc; entities: name asc) is applied.

---

### User Story 3 - Database container refuses to start without a password (Priority: P3)

A developer starts the stack without `POSTGRES_PASSWORD` configured. Today the database silently runs with the guessable password `myths`.

**Why this priority**: Closes the "no insecure defaults" gap; affects only misconfigured setups.

**Independent Test**: Run the compose config validation with `POSTGRES_PASSWORD` unset and verify it aborts with the required message; with it set, validation succeeds.

**Acceptance Scenarios**:

1. **Given** `POSTGRES_PASSWORD` is unset or empty, **When** the stack is brought up, **Then** startup aborts with "POSTGRES_PASSWORD is required: set it in .env (see .env.example)".
2. **Given** `POSTGRES_PASSWORD` is set in `.env`, **When** the stack starts, **Then** it behaves exactly as before.
3. **Given** the README, **When** a developer reads the variable table, **Then** it states the password is required with no default.

### Edge Cases

- `order` in upper case (`DESC`): rejected with 422 (allowed values are lower case only; categories and sources already behave this way).
- Sorting ties (users with equal `full_name`, entities with equal `created_at`): a secondary sort by `id` keeps pagination stable.
- `sort=full_name` on users where `full_name` is null: rows with a null value are always listed last, in both directions and on every database engine, and no row is lost or duplicated across pages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `GET /countries` MUST accept `sort` only from {name, id}, default name; any other value returns 422.
- **FR-002**: `GET /countries` MUST accept `order` only from {asc, desc}, default asc; any other value returns 422.
- **FR-003**: The `relations` parameter MUST be removed from `GET /countries` and `GET /countries/{id}`; a request that still sends it MUST NOT fail.
- **FR-004**: `GET /users` MUST accept `sort` only from {id, email, full_name}, default email, and `order` only from {asc, desc}, default asc; other values return 422.
- **FR-005**: `GET /users` MUST return results ordered by the requested field and direction, applied before pagination, with null values last and `id` as tie-breaker.
- **FR-006**: `GET /entities` MUST accept `sort` only from a fixed set of real entity fields {id, name, created_at}, default name, and `order` only from {asc, desc}, default asc; other values return 422.
- **FR-007**: `GET /entities` MUST return results ordered as requested, applied before pagination, with null values last and `id` as tie-breaker.
- **FR-008**: Validation failures MUST use the project's standard error envelope and MUST NOT expose internal details (attribute names, stack traces).
- **FR-009**: The database service in the compose file MUST NOT define a default password; without `POSTGRES_PASSWORD` startup aborts with the message "POSTGRES_PASSWORD is required: set it in .env (see .env.example)".
- **FR-010**: README MUST document `POSTGRES_PASSWORD` as required with no default.
- **FR-011**: The observable behavior of categories, entity-types and sources lists (accepted values, default order, responses) MUST NOT change, even though they adopt the shared sorting helper; the reset-password rate limit, limiter docstring and `Settings()` tests MUST remain untouched.

### Key Entities

- **Country**: sortable by name, id; has no relationships to include.
- **User**: sortable by id, email, full_name; listed only by superusers.
- **Entity**: sortable by id, name, created_at; filtered by type, category, active flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of requests to the three list endpoints with a sort or order value outside the allowed set get a client error (422) and none produces a server error.
- **SC-002**: For every allowed sort field and both directions, the users and entities lists return rows in the requested order across all pages with no duplicates or omissions.
- **SC-003**: Starting the stack without a database password fails immediately with a message that names the missing variable and where to set it, and CI fails if that guard is ever removed.
- **SC-004**: Existing tests for unchanged endpoints keep passing and total coverage does not drop below the project gate.
- **SC-005**: Items 2 and 5 of issue #54 can be closed with evidence; items 1, 3 and 4 are closed referencing the existing code.

## Assumptions

- The current default sort of each list is preserved (countries: name, users: email, entities: name), so existing clients see no change when they send no parameters.
- Changing from "ignored" or "silent fallback" to 422 for invalid `sort`/`order` is acceptable for a pre-1.0 API; categories, entity-types and sources already behave this way.
- Developers already have `POSTGRES_PASSWORD` in `.env` because the application refuses to start without it, so the compose change breaks only setups without a `.env`.
- CI does not rely on the compose default (it passes its own password).
- Entity `sort` allows id, name and created_at only; other columns (long text, flags) are not useful sort keys.
- Verified 2026-11-25: `Country` has only id, name, status and `User` has no `created_at`; the old OpenAPI examples advertised `created_at` and it silently fell back to `id`. It is not offered for those two lists and no migration is added for it.

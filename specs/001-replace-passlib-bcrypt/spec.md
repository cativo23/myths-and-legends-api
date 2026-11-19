# Feature Specification: Replace passlib with direct bcrypt

**Feature Branch**: `chore/tooling-reproducibility` (spec directory is independent of branch name)

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Replace the abandoned passlib dependency with the bcrypt library used directly for password hashing and verification in app/core/security.py. Remove the bcrypt monkeypatch (__about__ shim and hashpw truncation wrapper). Existing stored $2b$ password hashes MUST keep verifying with no migration; passwords longer than 72 bytes keep the current truncating behavior explicitly; bcrypt is capped to >=5,<6 and passlib is removed from requirements.txt. Public function behavior (get_password_hash, verify_password) is unchanged. No API contract changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Existing users keep logging in (Priority: P1)

Every user whose password was stored before this change signs in with the same password and the same result. No password reset, no forced re-registration, no visible difference.

**Why this priority**: A regression here locks every existing account (including the first superuser) out of the API. It is the only way this change can hurt users.

**Independent Test**: Verify a set of fixed, previously generated stored password hashes (captured from the current implementation) against their known passwords, and against wrong passwords. Delivers value on its own: it proves backward compatibility without any other change.

**Acceptance Scenarios**:

1. **Given** a stored password hash produced by the current implementation, **When** the user presents the correct password, **Then** verification succeeds.
2. **Given** the same stored hash, **When** the user presents an incorrect password, **Then** verification fails.
3. **Given** a stored hash and a password containing non-ASCII characters (accents, emoji), **When** the correct password is presented, **Then** verification succeeds.

---

### User Story 2 - New and changed passwords stay interoperable (Priority: P1)

Passwords set after this change (registration, password update, password reset) are stored in the same standard format as before and verify correctly, including long passwords.

**Why this priority**: Equal in weight to Story 1: hashes written now must remain readable by any rollback to the previous version and by any standard bcrypt verifier.

**Independent Test**: Hash a password, confirm the stored value has the same standard format and cost as before, verify it back, and confirm two hashes of the same password differ (salted).

**Acceptance Scenarios**:

1. **Given** a new password, **When** it is hashed, **Then** the result is a standard bcrypt hash with the same identifier prefix and cost factor as hashes produced today.
2. **Given** a hash just produced, **When** the same password is verified, **Then** verification succeeds.
3. **Given** a password longer than 72 bytes, **When** it is hashed and verified, **Then** it behaves as today: only the first 72 bytes are significant, and no error is raised.

---

### User Story 3 - The project no longer depends on abandoned or patched code (Priority: P2)

A maintainer installing the project gets no unmaintained password library and no runtime patching of third-party internals. The dependency set resolves to a supported bcrypt major version.

**Why this priority**: This is the motivation (supply-chain and upgrade risk), but it delivers no user-visible value until Stories 1 and 2 hold.

**Independent Test**: Inspect the dependency list and the security module: the old library is absent, no code mutates the bcrypt module at import time, and the test suite passes on a clean install.

**Acceptance Scenarios**:

1. **Given** a clean install from the dependency list, **When** the application starts, **Then** it starts without the old library installed.
2. **Given** the security module, **When** it is imported, **Then** it does not modify any third-party module.

---

### Edge Cases

- A password of exactly 72 bytes, 73 bytes, and much longer: results must match today's truncating behavior.
- A multi-byte character that straddles the 72-byte boundary: truncation happens on bytes, as today, and must not raise.
- An empty password: behaves as today.
- A stored value that is not a valid bcrypt hash (corrupted, empty, or from another scheme): verification must fail closed (return failure), never authenticate and never surface an internal error to the client.
- A password containing a NUL byte: hashes and verifies normally as a distinct secret (the old library rejected it, which could surface as a server error); verification against an unrelated hash fails.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST verify every password hash produced by the current implementation, with no migration or rehash step.
- **FR-002**: The system MUST store newly hashed passwords in the same standard bcrypt format and cost factor currently in use, salted so that equal passwords produce different hashes.
- **FR-003**: The system MUST treat only the first 72 bytes of a password as significant, truncating explicitly and without error, identically for hashing and verification.
- **FR-004**: The system MUST fail closed when verifying against an invalid or non-bcrypt stored value: return failure, never authenticate, never raise to the caller.
- **FR-005**: The public functions `get_password_hash` and `verify_password` MUST keep their names, signatures, and return types, so no caller changes.
- **FR-006**: The security module MUST NOT patch or mutate any third-party module at import time.
- **FR-007**: The project MUST NOT depend on the abandoned password-hashing library; the bcrypt dependency MUST be bounded to the supported major version (>=5,<6).
- **FR-008**: Authentication behavior observable through the API (login, user create/update, password reset) MUST be unchanged; no endpoint contract changes.

### Key Entities

- **Stored password hash**: the value persisted on a user record; an opaque bcrypt string. Its format must not change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of a fixed fixture of pre-change stored hashes verify against their original passwords, and 0% verify against wrong passwords.
- **SC-002**: The full existing test suite passes unchanged (254 tests today) with coverage still above the project gate.
- **SC-003**: A hash produced after the change verifies under the previous implementation (rollback safety), demonstrated once during verification.
- **SC-004**: Zero third-party modules are modified at import time, and the abandoned library is absent from the installed dependency set.
- **SC-005**: Login latency for a typical request is not noticeably different (same cost factor; no extra hashing work).

## Assumptions

- The current cost factor is the library default in use today (confirmed by inspecting a hash produced by the current code during planning); it is preserved, not tuned, in this change.
- "Fail closed" on malformed stored hashes (FR-004) is a deliberate small hardening over today's behavior, where the old library may raise. No endpoint currently relies on that exception.
- NUL-byte passwords: the old library rejected them; the replacement handles them correctly (verified against bcrypt 5.0.0 during implementation). Accepting them is a deliberate delta: it removes a latent server-error path, and adding a rejection would be new code with no benefit.
- Rehash-on-login to a higher cost factor is out of scope (no cost change, YAGNI).
- Only `app/core/security.py` uses the old library (verified by search); no other module changes.
- Dependency pinning and the lockfile are handled by a separate step of the same session and are not part of this spec.

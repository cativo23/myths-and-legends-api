---
description: "Task list for replacing passlib with direct bcrypt"
---

# Tasks: Replace passlib with direct bcrypt

**Input**: Design documents from `/specs/001-replace-passlib-bcrypt/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md (no entities change), quickstart.md

**Tests**: REQUIRED (constitution Principle I). Characterization tests are committed green against the *current* implementation first, then new-behavior tests are committed red, then the swap turns them green.

**Organization**: Grouped by user story. US1 and US2 share one code path (`app/core/security.py`), so the single swap task sits in the US3 phase and is the step that turns every earlier red test green.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (baseline on the OLD implementation)

- [X] T001 Run `./myths test tests/test_security.py --no-cov` and record that it is green before any change
- [X] T002 Generate fixture data with the current code via `./myths python`: ~4 bcrypt hashes (ASCII password, accented/emoji password, empty password, an exactly-72-byte password) plus one `$2y$` variant; keep only throwaway dummy passwords. Paste the (hash, password) pairs as constants at the top of `tests/test_security.py`

---

## Phase 2: Foundational

None. No schema, config, or dependency change blocks the stories.

---

## Phase 3: User Story 1 - Existing users keep logging in (Priority: P1)

**Goal**: Pre-change hashes verify; wrong passwords fail; malformed stored hashes fail closed.

**Independent Test**: `./myths test tests/test_security.py --no-cov -k "verify"`

### Tests

- [X] T003 [P] [US1] Add `should_verify_pre_change_hashes` (parametrized over T002 fixtures, incl. unicode, empty, `$2y$`) in `tests/test_security.py` — green on old code (FR-001)
- [X] T004 [P] [US1] Add `should_reject_wrong_password_against_pre_change_hash` in `tests/test_security.py` — green on old code (SC-001)
- [X] T005 [P] [US1] Add `should_fail_closed_on_malformed_stored_hash` parametrized over `"notahash"`, `""`, `None`, `"$2b$12$short"` and a NUL-byte password, asserting `verify_password(...) is False` and no exception, in `tests/test_security.py` — write this together with T012 (after T011) so no test stays uncommitted across commits; RED on old code, confirm the failure is `UnknownHashError`/`ValueError`, not a typo (FR-004)
- [X] T006 [US1] Commit T002–T004 (fixtures plus characterization tests) as green (`test(security): characterize password hashing before replacing passlib`)

---

## Phase 4: User Story 2 - New and changed passwords stay interoperable (Priority: P1)

**Goal**: New hashes are `$2b$`, cost 12, salted, with explicit 72-byte truncation.

**Independent Test**: `./myths test tests/test_security.py --no-cov -k "hash"`

### Tests

- [X] T007 [P] [US2] Add `should_produce_standard_bcrypt_hash_with_cost_12` (prefix `$2b$12$`, length 60) in `tests/test_security.py` — green on old code (FR-002)
- [X] T008 [P] [US2] Add `should_salt_each_hash` (two hashes of one password differ, both verify) in `tests/test_security.py` — green on old code (FR-002)
- [X] T009 [P] [US2] Add `should_treat_only_first_72_bytes_as_significant` covering 72, 73, 200 bytes and a multibyte character straddling byte 72; hashing and verifying never raise and a 72-byte hash verifies the longer original in `tests/test_security.py` — green on old code (FR-003)
- [X] T010 [P] [US2] Add a NUL-byte hashing test in `tests/test_security.py` — written as rejection on old code, replaced after the swap by `should_hash_and_verify_password_containing_nul_byte` (plan decision 5, revised)
- [X] T011 [US2] Commit T007–T010 (`test(security): pin hash format, salt and 72-byte truncation`)

---

## Phase 5: User Story 3 - No abandoned or patched dependency (Priority: P2)

**Goal**: passlib gone, no import-time patching, bcrypt bounded to `>=5,<6`; makes all earlier tests pass on the new code.

**Independent Test**: `./myths test` is green and `pip show passlib` finds nothing after a rebuild.

### Tests (red first)

- [X] T012 [US3] First write T005 here. Then add `should_not_patch_bcrypt_at_import` in `tests/test_security.py`: in a fresh subprocess, import `bcrypt` and `app.core.security`, assert `not hasattr(bcrypt, "__about__")` and `bcrypt.hashpw.__module__` is not `app.core.security` — RED on old code (FR-006)
- [X] T013 [US3] Run the new tests T005 and T012 and confirm they fail for the right reason (record the output in the commit message body); commit as `test(security): add failing tests for fail-closed verify and no import-time patch`

### Implementation

- [X] T014 [US3] Rewrite `get_password_hash` and `verify_password` and delete the monkeypatch block and the passlib import in `app/core/security.py`, following the Design section of plan.md (`_BCRYPT_ROUNDS = 12`, `_BCRYPT_MAX_BYTES = 72`, one `_to_bcrypt_input` helper, `except ValueError` returning `False`); keep a one-line WHY comment for truncation and for fail-closed (FR-003, FR-004, FR-006)
- [X] T015 [US3] In `requirements.txt` replace `passlib[bcrypt]>=1.7.4,<2` with `bcrypt>=5,<6` (FR-007)
- [X] T016 [US3] Rebuild and run `./myths build` then `./myths test`; all tests including T003–T012 pass, coverage ≥ 68%, `./myths python -m pip show passlib` reports not found, and `grep -rn passlib app tests requirements.txt` finds nothing
- [X] T017 [US3] Commit T014–T015 (`refactor(security): replace passlib with direct bcrypt`, body explains why: unmaintained, needed a monkeypatch for bcrypt 5)

---

## Phase 6: Polish & Cross-Cutting

- [X] T018 Rollback-safety check (SC-003, one-off, not committed): hash a password with the new code, then verify it with the previous commit's implementation (`git stash`/worktree of `HEAD~1`); both agree
- [X] T019 Login smoke per quickstart step 6: seeded superuser `POST /api/v1/auth/login` returns 200 against the running stack (no secrets printed)
- [X] T020 Add a CHANGELOG `[Unreleased]` entry under Changed (passlib removed, bcrypt direct, malformed hashes now fail closed) in `CHANGELOG.md`, and replace `passlib/bcrypt` with `bcrypt` in the Key Technologies list of `CLAUDE.md`
- [X] T021 Self-review the full diff as if written by someone else; run `/speckit-converge`

---

## Dependencies & Order

- T001 → T002 → US1 tests (T003–T005) → T006 → US2 tests (T007–T010) → T011 → T012 → T013 → T014 → T015 → T016 → T017 → Polish.
- T014 is the only task that changes `app/`; everything before it only adds tests (no behavior change), which is what makes the swap provably safe.
- Parallel: T003, T004, T005 touch one file but are independent test functions (write together); same for T007–T010.

## Implementation Strategy

MVP is US1 + US2 characterization on the old code (nothing ships broken), then the swap. If T013 shows an unexpected failure shape, stop and revisit plan.md before T014.

## Phase 7: Convergence

- [X] T022 Restore the `verify_password` parameter annotation to `hashed_password: str` in `app/core/security.py` (keep the runtime `if not hashed_password` guard) per FR-005 (contradicts)

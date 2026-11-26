---
description: "Task list for end-to-end user-flow tests"
---

# Tasks: End-to-end user-flow tests

**Input**: `/specs/007-e2e-user-flows/` (plan.md, spec.md, research.md, data-model.md, quickstart.md; no contracts, no app code changes)

**Tests**: The deliverable IS tests. Test-First adaptation (plan.md, Constitution I): after a test passes, temporarily break the behavior it guards, see it fail for the right reason, then restore (record the check in the commit body or task notes). Use only the existing `client`, `db`, `test_user`, `superuser`, `auth_headers`, `superuser_headers` fixtures. Do not run `black` on `tests/`. Do not run test commands in parallel in the same container.

**Organization**: One commit per concern. No new field constraints, so no `data-model.md` field citations are needed beyond `user.hashed_refresh_token` and `entity_relation.relation_type` (referenced in US1 and US2). If any journey exposes an app defect, STOP and ask Carlos (spec Assumptions).

## Phase 1: Setup

- [ ] T001 Baseline on the untouched branch: `./myths up -d`, `./myths test` green (444 passed, 85.71% expected), `uvx black --check app`

## Phase 2: Foundational — committed together with US1 (the marker is never committed unused)

- [ ] T002 Register the `e2e` marker in `pytest.ini` under `markers` (`e2e: End-to-end user journeys`); required by `--strict-markers` (research.md D2)
- [ ] T003 Create `tests/e2e/__init__.py` and `tests/e2e/conftest.py` with a `pytest_collection_modifyitems` hook that adds the `e2e` marker to every item under `tests/e2e/` (research.md D2)
- [ ] T004 Manual verification, no permanent test: once T005 exists, check that `./myths test -m e2e --no-cov` collects it and `./myths test -m "not e2e" --no-cov --collect-only -q` does not (quickstart step 2)

## Phase 3: User Story 1 — Entity and relations journey (P1) — commit `test(e2e): cover the entity graph journey`

**Goal**: a superuser builds, reads and prunes a graph; every step's result is visible in later reads.
**Independent test**: `./myths test tests/e2e/test_entity_graph_journey.py --no-cov`.

- [ ] T005 [US1] In `tests/e2e/conftest.py` add small plain helper functions that create a category, an entity type, an entity and a relation through the API with `superuser_headers` and return the response JSON (no new helper module). Then, in `tests/e2e/test_entity_graph_journey.py`, write `test_should_build_read_and_prune_a_relation_graph`: create category and entity type and assert each is retrievable by GET, create at least four entities and assert each is retrievable and references that category and type, create one relation of each kind (a symmetric one such as SIBLINGS and directed ones such as MOTHER_CHILD and GUARDIAN_PLACE), then assert via `GET /entities/{id}/relations` and `GET /entities/{id}` that each entity sees exactly its edges (symmetric on both ends with each end's own row id, directed once on each end with correct direction), per `data-model.md` `entity_relation.relation_type`. Do not repeat the per-endpoint checks already in `tests/domains/test_entities.py`
- [ ] T006 [US1] In the same file, write `test_should_remove_only_the_deleted_relation_from_the_graph`: delete the symmetric relation through `DELETE /entities/{id}/relations/{relation_id}` and assert it is gone from both entities' details while directed relations and all entities remain; then delete a directed relation and assert only it disappears
- [ ] T007 [US1] In the same file, write `test_should_leave_the_graph_untouched_when_a_regular_user_tries_to_write`: with `auth_headers` attempt to create an entity, create a relation and delete a relation; assert 403 each time and the graph unchanged
- [ ] T008 [US1] Red check: temporarily make symmetric creation or deletion touch only one row (e.g. skip the reverse row in `remove_with_reverse`), confirm T005/T006 fail for the right reason, restore with `git checkout -- app`

## Phase 4: User Story 2 — Authentication session journey (P1) — commit `test(e2e): cover the auth session journey`

**Goal**: login → refresh → reuse rejected → one session per user → logout.
**Independent test**: `./myths test tests/e2e/test_auth_session_journey.py --no-cov`.

- [ ] T009 [US2] In `tests/e2e/test_auth_session_journey.py`, write `test_should_keep_a_session_alive_across_refreshes_until_logout`: login, use the access token on `/auth/me`, refresh (new pair works on `/auth/me`), refresh again with the new token, then logout and assert the latest refresh token is rejected (401). Chain tokens from each previous step; do not re-assert malformed/expired-token cases
- [ ] T010 [US2] In the same file, write `test_should_reject_a_reused_refresh_token_without_revoking_the_newer_session`: after one rotation, the first token returns 401 and the token from the rotation still refreshes successfully (research.md D5; `user.hashed_refresh_token` unchanged by the failed reuse)
- [ ] T011 [US2] In the same file, write `test_should_allow_only_one_active_session_per_user`: log in twice with the same credentials, assert the first session's refresh token is rejected (401) and the second's works (`user.hashed_refresh_token` is replaced on login). Note that a gap, not covered anywhere else
- [ ] T012 [US2] Red check: temporarily stop overwriting the stored refresh hash on login, or stop clearing it on logout, confirm T009/T011 fail for the right reason, restore with `git checkout -- app`

## Phase 5: User Story 3 — Rate-limit boundaries (P2) — commit `test(e2e): cover rate-limit boundaries`

**Goal**: exact 429 boundary on the four missing endpoints, without leaking state to other tests.
**Independent test**: `./myths test tests/e2e/test_rate_limit_boundaries.py --no-cov`, then another module right after (quickstart step 3).

- [ ] T013 [US3] In `tests/e2e/test_rate_limit_boundaries.py`, write `test_should_return_429_on_password_recovery_after_the_auth_limit`: `POST /auth/password-recovery/{email}` with a non-existent email `settings.RATE_LIMIT_AUTH_PER_MINUTE` times (none 429), then once more: 429 with a valid JSON body (research.md D3)
- [ ] T014 [US3] Same file, `test_should_return_429_on_password_reset_after_the_auth_limit`: `POST /auth/reset-password/` with a well-formed body (invalid `token`, valid-shaped `new_password`) `settings.RATE_LIMIT_AUTH_PER_MINUTE` times (all 400, none 429), then 429 with a valid JSON body
- [ ] T015 [US3] Same file, `test_should_return_429_on_refresh_after_the_default_limit`: `POST /auth/refresh` with an invalid token `settings.RATE_LIMIT_PER_MINUTE` times (none 429), then 429
- [ ] T016 [US3] Same file, `test_should_return_429_on_logout_after_the_default_limit`: unauthenticated `POST /auth/logout` `settings.RATE_LIMIT_PER_MINUTE` times (none 429), then 429
- [ ] T017 [US3] No order-dependent test. Verify isolation (FR-004, US3 scenario 3) by running `./myths test tests/e2e/test_rate_limit_boundaries.py --no-cov` and immediately `./myths test tests/e2e/test_auth_session_journey.py --no-cov`; the second must pass. The guarantee is the existing autouse `limiter.reset()` in `tests/conftest.py`
- [ ] T018 [US3] Red check: temporarily lower the loop count of one boundary test by one and confirm the 429 assertion fails (the last allowed request would no longer be the one before the limit), then restore. Then repeat the T017 chained run to prove no leakage

## Phase 6: Polish — commit `docs(roadmap): close session 1.6`

- [ ] T019 `uvx black --check app` and full `./myths test` (coverage gate; compare against 444 passed / 85.71%); confirm `-m e2e` and `-m "not e2e"` select as expected (quickstart); review own diff (including that no assertion repeats `tests/domains/` coverage, FR-007, and that tests are order-independent, FR-008), then run superpowers:code-reviewer on the diff
- [ ] T020 Update `docs/ROADMAP.md`: mark 1.6 done with summary and decisions (in-process, `tests/e2e/`, `e2e` marker, scope vs issue #31, gaps covered); keep notes of pending items intact
- [ ] T021 Push, PR against `develop`, wait for green CI, `gh pr merge --admin --merge --delete-branch`, confirm CI on develop; check in the CI log that `tests/e2e` tests ran and that total test time is within 10% of the latest green `develop` run (SC-004); close #31 by hand with evidence and a note on obsolete criteria (register flow, country CRUD, location/source journey, separate DB); then write the prompt for session 2.1 from `docs/ROADMAP.md`

## Dependencies

Phase 1 → Phase 2 → Phases 3, 4, 5 (independent of each other; run in priority order US1, US2, US3) → Phase 6. No task is parallelizable: tests of each story share a file. Never run test commands in parallel in one container.

## Implementation Strategy

MVP is US1 (T001–T008): it also proves the marker mechanism. Then US2 (fills the one-session gap), then US3. Commit after each phase with the commit message given in the phase title. If a journey fails against current behavior, stop and report instead of editing app code.

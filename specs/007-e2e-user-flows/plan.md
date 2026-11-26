# Implementation Plan: End-to-end user-flow tests

**Branch**: `test/e2e-user-flows` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

## Summary

Add a `tests/e2e/` package with three test modules (entity graph journey, auth session journey, rate-limit boundaries) and register an `e2e` marker in `pytest.ini`. Tests go through HTTP only (`TestClient`) on the existing per-test SQLite database, reuse the `client`, `test_user`, `superuser`, `*_headers` fixtures, and add one small shared helper module for the journey's repetitive setup. **No application code changes.** Limits are read from `settings`; isolation between tests is the existing autouse `limiter.reset()`.

## Technical Context

**Language/Version**: Python 3.10 (lock target), FastAPI 0.135
**Primary Dependencies**: pytest, starlette `TestClient` (no new dependencies)
**Storage**: SQLite per test (existing `db` fixture); no schema change, no migration
**Testing**: `./myths test tests/e2e --no-cov` or `-m e2e`; full suite `./myths test`
**Target Platform**: Linux container / GitHub Actions
**Project Type**: web-service (test-only change)
**Performance Goals**: E2E adds roughly 100 requests (the 61-call refresh/logout loops dominate); well under the 10% CI-time bound
**Constraints**: `--strict-markers` is on, so the marker must be registered; do not run `black` on `tests/`; sync tests only
**Scale/Scope**: 3 modules, about 12 tests, 1 helper module, 1 line in `pytest.ini`, ROADMAP update

## Constitution Check

| Principle | Status | Note |
|---|---|---|
| I Test-First | Pass (adapted) | The deliverable is the tests. Red is obtained for each new assertion by temporarily breaking the behavior it guards (e.g. clearing the stored refresh token on login, dropping the reverse-row delete) and seeing the test fail for the right reason, then restoring. Names describe behavior. No third-party mocks |
| II Security-First | Pass | No secrets: tokens come from live logins, passwords from existing fixtures; recover test uses a non-existent email so no mail is sent; no ids or tokens asserted in logs |
| III Minimalism | Pass | No new dependency, no new fixture framework, no per-test DB. One helper module only for setup that would otherwise repeat in all entity-journey tests |
| IV Layered/sync | Pass | No app code touched; tests are plain sync `def` |
| V Migrations | N/A | No schema change |

Post-design re-check: unchanged, all pass.

## Project Structure

### Documentation (this feature)

```text
specs/007-e2e-user-flows/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md   # /speckit-tasks
```

`contracts/` is skipped: the feature exposes no new interface.

### Source Code

```text
pytest.ini                         # + marker: e2e
tests/e2e/
├── __init__.py
├── conftest.py                    # applies the e2e marker to every test in the package
├── test_entity_graph_journey.py   # US1
├── test_auth_session_journey.py   # US2
└── test_rate_limit_boundaries.py  # US3
docs/ROADMAP.md                    # close 1.6
```

**Structure Decision**: a dedicated `tests/e2e/` directory (decided with Carlos). Markers are applied once in `tests/e2e/conftest.py` via `pytest_collection_modifyitems`, so no per-test decorators can be forgotten. Journey setup helpers (create category/type/entity/relation through the API) live in `tests/e2e/conftest.py` as plain functions or fixtures, not in a separate helpers module, to avoid a new file.

## Complexity Tracking

None.

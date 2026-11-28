# Implementation Plan: API freeze for v0.2.0

**Branch**: `feat/api-freeze-v0-2-0` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

## Summary

Close the API contract before the frontend consumes it: one 429 body (root cause: an `async` handler that slowapi's middleware silently replaces), one line per symmetric relation (shared summary builder used by both relation-reading endpoints), an optional `image_credit` on entities (nullable column, reversible migration), a typed and timezone-aware `expires_at`, Salvadoran docs and examples guarded by a test, a Fair Use note, CHANGELOG, ROADMAP and, after merge and confirmation, the `v0.2.0` tag. One branch, one PR, one commit per risk.

## Technical Context

**Language/Version**: Python 3.10 (lock target), FastAPI 0.135, Pydantic 2
**Primary Dependencies**: slowapi, SQLAlchemy 2.0, Alembic (no new dependencies)
**Storage**: PostgreSQL 15; one nullable column added to `entity`
**Testing**: `./myths test` (full, 68% gate), `./myths test <file> --no-cov`; E2E marker `e2e`; migration checked up, down, up on PostgreSQL via `./myths alembic`
**Target Platform**: Linux container / GitHub Actions
**Project Type**: web-service
**Performance Goals**: none; dedup is in memory over a handful of relation rows
**Constraints**: sync `def` handlers and endpoints; `HTTPException` envelope; do not run `black` on `tests/`; no `requirements` changes
**Scale/Scope**: about 10 source files touched, 1 migration, ~15 tests changed or added, 3 docs files

## Constitution Check (v1.0.0)

| Principle | Status | Note |
|---|---|---|
| I Test-First | Pass | Each risk starts with a failing test seen failing for the right reason (429 default body, duplicated symmetric rows, missing `image_credit`, `expires_at` format and offset, OpenAPI scan for foreign mythologies). The existing E2E tests that pin the old behavior are first changed to the new expectation (Red), then the code follows (Green). No third-party mocks |
| II Security-First | Pass | Error bodies carry no internals; `image_credit` is validated at the boundary (length, trim) and writes stay superuser-only; `retry_after` leaks only the public limit window; Fair Use text holds no secrets or contact PII beyond what `app/main.py` already publishes |
| III Minimalism | Pass, with two flags | (a) `retry_after` real value (R2) goes beyond the shape and is a separate commit; (b) dedup also applied to `/entities/{id}/relations` (R3), which also removes a duplicated loop. Both are raised for Carlos. No new abstractions beyond one shared summary function that replaces two copies |
| IV Layered | Pass | The summary builder lives in the entity relation service, endpoints stay thin, handler stays sync, errors stay `detail` |
| V Migrations | Pass | One Alembic revision with `downgrade`, verified up, down, up on PostgreSQL |

No violations; Complexity Tracking not needed. Re-check after design: unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/008-api-freeze-v0-2-0/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api-changes.md
├── checklists/requirements.md
└── tasks.md            # created by /speckit-tasks
```

### Source Code (touched)

```text
app/api/common/middleware/rate_limiter.py          # sync handler, real retry_after (R1, R2)
app/api/v1/domains/entities/models/entity.py       # image_credit column (R4)
app/api/v1/domains/entities/schemas/entity.py      # image_credit, Salvadoran examples
app/api/v1/domains/entities/schemas/entity_type.py # Salvadoran examples
app/api/v1/domains/entities/endpoints/entities.py  # use shared summary builder; type-filter text; image_credit in detail
app/api/v1/domains/entities/endpoints/entity_types.py
app/api/v1/domains/entities/services/entity_relation.py   # shared symmetric-aware summary builder (R3)
app/api/v1/domains/users/schemas/token.py          # expires_at: datetime
app/core/security.py                               # aware-UTC get_token_expiry (R5)
app/main.py                                        # Fair Use note; description for the real catalog
alembic/versions/<rev>_add_entity_image_credit.py
README.md, CHANGELOG.md, docs/ROADMAP.md, CLAUDE.md (only if stale statements are found)
tests/e2e/*, tests/domains/test_entities.py, tests/domains/... (new tests per risk)
```

**Structure Decision**: existing layout; no new modules. One new migration and one new test module for the OpenAPI scan.

## Commit sequence (one concern each)

1. `docs(spec): add spec, plan and tasks for the v0.2.0 freeze`
2. `fix(rate-limit): return one 429 body for every limit` (R1, with tests)
3. `feat(rate-limit): report seconds until the window resets in retry_after` (R2)
4. `fix(entities): list each symmetric relation once` (R3)
5. `feat(entities): add optional image credit` (R4, with migration)
6. `fix(auth): type expires_at as an aware UTC datetime` (R5)
7. `docs(api): describe the Salvadoran catalog and add a Fair Use note` (R6, with the OpenAPI scan test)
8. `docs: close session 1.7 in changelog and roadmap`

## Risks and notes

- The 1.6 E2E tests will fail by design when the behavior changes; they are edited in the same commit as the fix, never skipped.
- `get_token_expiry` becoming timezone-aware may affect any comparison with `datetime.utcnow()`; tasks include a grep and test run before the commit.
- The tag is **not** part of the PR: it is created after merge, only on Carlos's confirmation.
- `CLAUDE.md` says "Image upload is integrated into entity create/update", but entity create/update take only `image_url`; upload is in the separate `images` domain. Verified in R4; fixed in CLAUDE.md only if Carlos agrees (it is a docs-only line).

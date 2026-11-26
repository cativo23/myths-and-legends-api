# Implementation Plan: Delete an entity relation

**Branch**: `feature/delete-entity-relation` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

## Summary

Add `DELETE /entities/{id}/relations/{relation_id}` (superuser, 204). A service method finds the relation only if it involves the path entity (origin or destination) and removes it; for symmetric types (SIBLINGS/ALLIES/ENEMIES) it also removes the reverse row in the same commit. **No duplicated code:** the symmetric-type list currently lives inline in `create_bidirectional`; it is extracted to one constant in `enums.py` and used by both create and delete.

## Technical Context

**Language/Version**: Python 3.10 (lock target), FastAPI 0.135, Pydantic 2.x
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 sync `Session` (no new dependencies)
**Storage**: PostgreSQL 15; no schema change, no migration; tests on SQLite
**Testing**: pytest via `./myths test` / `./myths test tests/domains/test_entities.py --no-cov`
**Target Platform**: Linux container (docker compose)
**Project Type**: web-service
**Performance Goals**: none; one indexed lookup + one commit
**Constraints**: sync `def`, `HTTPException` envelope, `Annotated` deps, auth dependency before lookup
**Scale/Scope**: 1 endpoint, 1 constant, 2 service methods, tests, ROADMAP

## Constitution Check

| Principle | Status | Note |
|---|---|---|
| I Test-First | Pass | Service and endpoint tests written and seen failing before code (see tasks) |
| II Security-First | Pass | `get_current_active_superuser` on the route; 401/403 precede lookups; one "Relation not found" message for missing and foreign relations; no ids echoed in errors; `gt=0` path params |
| III Minimalism | Pass | No audit log, no update endpoint, no migration; one shared constant removes an inline duplicate |
| IV Layered/sync | Pass | Logic in `EntityRelationService`; endpoint thin `def`; `HTTPException` |
| V Migrations | N/A | No schema change (FK already `ON DELETE CASCADE`) |

Post-design re-check: unchanged, all pass.

## Project Structure

### Documentation (this feature)

```text
specs/006-delete-entity-relation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/delete-entity-relation.md
└── tasks.md   # /speckit-tasks
```

### Source Code

```text
app/api/v1/domains/entities/
├── enums.py                      # + SYMMETRIC_RELATION_TYPES
├── services/entity_relation.py   # use constant; + get_for_entity, + remove_with_reverse
└── endpoints/entities.py         # + DELETE /{id}/relations/{relation_id}
tests/domains/test_entities.py    # service + endpoint tests
docs/ROADMAP.md                   # close 1.5, add audit follow-up
```

**Structure Decision**: existing domain layout; no new files in `app/`.

## Complexity Tracking

No violations.

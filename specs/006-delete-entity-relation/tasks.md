---
description: "Task list for deleting an entity relation"
---

# Tasks: Delete an entity relation

**Input**: `/specs/006-delete-entity-relation/` (plan.md, spec.md, research.md, data-model.md, contracts/delete-entity-relation.md, quickstart.md)

**Tests**: REQUIRED (Constitution Principle I). Each task writes its failing test first and confirms it fails for the right reason. Tests use the existing `client`, `db`, `superuser_headers`, `auth_headers` fixtures (SQLite) in `tests/domains/test_entities.py`. Do not run `black` on `tests/`.

**Organization**: One commit per concern; a task's tests and code share a commit. No code duplication: one `SYMMETRIC_RELATION_TYPES` constant. No schema change, so no field citations beyond `data-model.md` `entity_relation.relation_type` (symmetric pairing rule).

## Phase 1: Setup

- [X] T001 Baseline on the untouched branch: `./myths up -d`, `./myths test` green (406 passed expected), `uvx black --check app`

## Phase 2: Foundational — commit `refactor(entities): share the symmetric relation types constant`

- [X] T002 Write a failing test in `tests/domains/test_entities.py` that `SYMMETRIC_RELATION_TYPES` equals `{SIBLINGS, ALLIES, ENEMIES}` and that creating each symmetric type yields two rows while MOTHER_CHILD/FATHER_CHILD/GUARDIAN_PLACE yield one (behavior pin; see data-model.md `entity_relation.relation_type`)
- [X] T003 Add `SYMMETRIC_RELATION_TYPES` (frozenset) after `RelationType` in `app/api/v1/domains/entities/enums.py` and replace the inline list in `create_bidirectional` in `app/api/v1/domains/entities/services/entity_relation.py` (research.md D4); T002 green, existing relation tests stay green

## Phase 3: User Story 1 — Remove a wrong relation (P1) — commit `feat(entities): delete an entity relation`

**Goal**: superuser deletes a relation by id; symmetric pairs go together.
**Independent test**: create, delete, list; entities remain.

- [X] T004 [US1] Write failing service tests in `tests/domains/test_entities.py` for `EntityRelationService.get_for_entity` (finds by origin, by destination; `None` for foreign or missing id) and `remove_with_reverse` (symmetric removes both rows; non-symmetric removes one; symmetric with missing reverse removes the existing row; other relation types between the same pair untouched)
- [X] T005 [US1] Implement `get_for_entity(db, *, entity_id, relation_id)` and `remove_with_reverse(db, *, relation)` in `app/api/v1/domains/entities/services/entity_relation.py` (research.md D2, D3, D5: reverse by `(destination, origin, type)`, single commit, rollback on error); T004 green
- [X] T006 [US1] Write failing endpoint tests in `tests/domains/test_entities.py`: 204 deleting non-symmetric via origin; 204 deleting symmetric via either entity and either row id (both gone from both lists); 204 via destination path; second delete → 404; entities still exist
- [X] T007 [US1] Add `DELETE /{id}/relations/{relation_id}` in `app/api/v1/domains/entities/endpoints/entities.py` (`status_code=204`, `get_current_active_superuser`, `Path(gt=0)`, responses 204/401/403/404/422 per contracts/delete-entity-relation.md); T006 green

## Phase 4: User Story 2 — Clear errors, no leak (P1) — commit `test(entities): pin error paths of relation delete`

**Goal**: predictable errors; existence not revealed to unauthorized callers.
**Independent test**: status codes and messages per contract.

- [X] T008 [US2] Write tests in `tests/domains/test_entities.py` (expected to pass already; if any fails, fix in T007): no token → 401; non-superuser → 403 for both existing and nonexistent ids (identical status/body); missing entity → 404 "Entity not found"; missing relation and relation of another entity → 404 "Relation not found" with identical bodies and nothing deleted; `id=0`/`relation_id=0`/negative → 422

## Phase 5: Polish

- [X] T009 Update `docs/ROADMAP.md`: mark 1.5 done with a summary and decisions; add a follow-up item "auditoría transversal de escrituras (quién/qué se creó, modificó o borró)"; keep 1.6 as next
- [ ] T010 Run `uvx black --check app` and `./myths test` (full, coverage gate), review own diff, then superpowers:code-reviewer on the diff
- [ ] T011 Push, PR against `develop`, wait for green CI, `gh pr merge --admin --merge --delete-branch`, confirm CI on develop, then write the prompt for session 1.6 (E2E tests: entity+relations cycle, auth with refresh, rate limits; issue #31)

## Dependencies

Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5. US2 tests depend on the endpoint from US1. No parallel tasks (all touch the same files).

## Implementation Strategy

MVP = Phases 2–3 (endpoint working); Phase 4 locks the security/error contract. Total: 11 tasks.

# Research: Delete an entity relation

## D1. Implement vs discard
- **Decision**: Implement. **Why**: relations are create/list only; a wrong one is uncorrectable short of deleting the entity. **Alternative**: discard (rejected by Carlos).

## D2. Symmetric deletion
- **Decision**: delete the addressed row and its reverse, found by `(origin=row.destination, destination=row.origin, type=row.type)`, in one commit. The unique constraint `(origin, destination, type)` guarantees at most one reverse row. If the reverse is missing (legacy data) only the addressed row is deleted. **Alternative**: delete one row only (rejected: leaves A→B without B→A).

## D3. Ownership and leak control
- **Decision**: lookup `WHERE id = :relation_id AND (origin = :entity_id OR destination = :entity_id)`; no match → 404 "Relation not found" (same for missing and foreign). Entity existence is checked first with `entity.exists` → 404 "Entity not found", same as the sibling endpoints. Auth dependency resolves before the handler body, so non-superusers see 401/403 only.

## D4. Shared symmetric list
- **Decision**: `SYMMETRIC_RELATION_TYPES` (frozenset) in `enums.py` next to `RelationType`; `create_bidirectional` switches to it. **Alternative**: a `is_symmetric` property on the enum (rejected: more surface than needed).

## D5. Atomicity
- **Decision**: `db.delete(row)` for both, then one `db.commit()`; on `SQLAlchemyError` rollback and re-raise (surfaces as 500, nothing deleted). No bulk `DELETE` statement, to keep the ORM session consistent.

## D6. Audit
- **Decision**: none now; roadmap item for cross-cutting write audit.

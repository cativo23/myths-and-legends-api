# Data Model: API freeze for v0.2.0

## Entity (table `entity`)

New column:

| Column | Type | Null | Default | Validation (boundary) |
|---|---|---|---|---|
| `image_credit` | `VARCHAR(255)` | yes | none | trimmed; blank becomes `None`; max 255 on create and update |

- Create: optional, omitted means `NULL`.
- Update (partial): omitted keeps the stored value; explicit `""` or `null` clears it.
- Read (list, detail): always present, `null` when unset.
- Migration: `ADD COLUMN image_credit VARCHAR(255) NULL`; downgrade drops it. Existing rows need no backfill.

## Entity relation (table `entity_relation`)

No schema change. Symmetric types (SIBLINGS, ALLIES, ENEMIES) keep two stored rows (A→B, B→A). Reads present one summary per pair:

| Stored | Queried from A | Queried from B |
|---|---|---|
| A→B and B→A | one summary (A origin, related B) | one summary (B origin, related A) |
| only A→B (legacy) | one summary (origin) | one summary (destination) |
| directed A→B | one (origin) | one (destination) |

Pair key: `(relation_type, related_entity_id)`; the row where the queried entity is origin wins.

## Token response (not stored)

| Field | Before | After |
|---|---|---|
| `expires_at` | untyped | `datetime`, serialized ISO 8601 with UTC offset |

## Rate-limit error (not stored)

`{"detail": {"message": str, "type": "rate_limit_exceeded", "retry_after": int | null}}` for every 429.

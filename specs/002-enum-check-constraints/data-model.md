# Data Model: enum CHECK constraints

No new tables or columns. Five existing `String(50)` columns gain a named CHECK constraint;
nullability and indexes are unchanged.

| Table | Column | Constraint name | Allowed values (from enum) |
|---|---|---|---|
| `category` | `name` | `ck_category_name` | MYTH, LEGEND, TRADITION |
| `entity_type` | `name` | `ck_entity_type_name` | CHARACTER, PLACE, OBJECT, GROUP, EVENT |
| `characteristic` | `type` | `ck_characteristic_type` | PHYSICAL, APPEARANCE, ABILITY, WEAKNESS |
| `entity_relation` | `relation_type` | `ck_entity_relation_relation_type` | MOTHER_CHILD, FATHER_CHILD, SIBLINGS, GUARDIAN_PLACE, ENEMIES, ALLIES |
| `source` | `source_type` | `ck_source_source_type` | BOOK, ORAL_TRADITION, WEB, DOCUMENT |

Total allowed values: 3 + 5 + 4 + 6 + 4 = 22 (matches SC-002).

**Rules**
- Comparison is exact and case-sensitive; `''` and whitespace variants are rejected.
- NULL is not covered by these constraints (CHECK passes on NULL); the existing `NOT NULL`
  remains the guard.
- Source of truth for the sets: `app/api/v1/domains/entities/enums.py`. The migration keeps a
  frozen copy, kept honest by a sync test.

**Migration**: one revision, `down_revision = '0f2ce4cae13f'`. `upgrade`: pre-check, then 5×
`create_check_constraint`. `downgrade`: 5× `drop_constraint(type_='check')`.

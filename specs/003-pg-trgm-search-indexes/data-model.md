# Data Model: trigram search indexes

No tables, columns or constraints change. Only indexes and one extension.

## Extension

| Name | Action |
|---|---|
| `pg_trgm` | `CREATE EXTENSION IF NOT EXISTS` on upgrade; left installed on downgrade |

## Indexes

| Table | Index | Type | Column | Action on upgrade | Action on downgrade |
|---|---|---|---|---|---|
| `entity` | `ix_entity_name_trgm` | GIN, `gin_trgm_ops` | `name` | create | drop |
| `entity` | `ix_entity_description_trgm` | GIN, `gin_trgm_ops` | `description` | create | drop |
| `entity` | `ix_entity_origin_trgm` | GIN, `gin_trgm_ops` | `origin` | create | drop |
| `location` | `ix_location_department_trgm` | GIN, `gin_trgm_ops` | `department` | create | drop |
| `entity` | `ix_entity_description` | B-tree | `description` | **drop** | recreate (as in `bd728d1bc3f7`) |
| `entity` | `ix_entity_name` | B-tree | `name` | keep | keep |
| `location` | `ix_location_department` | B-tree (composite with `municipality` in migrated DBs) | `department` | keep | keep |

## Model change

`Entity.description`: `mapped_column(Text, nullable=True)` (drops `index=True`). GIN indexes are
**not** declared on models (SQLite `create_all` cannot build them).

## Ordering inside the migration

Upgrade: extension → four GIN indexes → drop `ix_entity_description` (the old index goes last so
there is no window without any index on `description`).
Downgrade: recreate `ix_entity_description` → drop four GIN indexes.

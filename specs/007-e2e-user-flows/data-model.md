# Data Model: End-to-end user-flow tests

No data model changes. The tests exercise existing models through the API:

| Entity | Used for | Notes |
|---|---|---|
| Category, EntityType | Reference data created at the start of the entity journey | Created by a superuser through the API |
| Entity | Nodes of the graph | Fresh names per test; no images |
| EntityRelation | Edges | Symmetric types (SIBLINGS, ALLIES, ENEMIES) yield 2 rows; MOTHER_CHILD, FATHER_CHILD, GUARDIAN_PLACE yield 1 row; list is `SYMMETRIC_RELATION_TYPES` in `entities/enums.py` |
| User (`hashed_refresh_token`) | Session state of the auth journey | One stored refresh hash per user; login replaces it, refresh rotates it, logout clears it |

State transitions covered:

- Session: logged-out → logged-in (hash set) → refreshed (hash rotated, old token dead) → re-logged-in (previous token dead) → logged-out (hash cleared).
- Relation: created → listed on both ends → deleted (symmetric: both rows gone; directed: one row gone).

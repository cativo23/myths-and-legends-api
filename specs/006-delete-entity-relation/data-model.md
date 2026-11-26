# Data Model: Delete an entity relation

No schema change. `entity_relation(id, entity_origin_id, entity_destination_id, relation_type, description)` with unique `(origin, destination, relation_type)` and `ON DELETE CASCADE` FKs to `entity`.

Pairing rule for symmetric types (SIBLINGS, ALLIES, ENEMIES): rows `(A,B,t)` and `(B,A,t)` exist together; the delete operation removes both. Non-symmetric types (MOTHER_CHILD, FATHER_CHILD, GUARDIAN_PLACE): one row.

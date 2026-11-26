# Contract: DELETE /api/v1/entities/{id}/relations/{relation_id}

Auth: Bearer token of an active superuser.

Path: `id` (int, > 0) entity; `relation_id` (int, > 0) relation, as shown by `GET /entities/{id}/relations`.

| Status | When | Body |
|---|---|---|
| 204 | Relation (and its reverse, if symmetric) deleted | none |
| 401 | Missing/invalid token | standard envelope |
| 403 | Not a superuser | standard envelope |
| 404 | Entity missing | `{"detail": "Entity not found"}` |
| 404 | Relation missing, or does not involve the entity | `{"detail": "Relation not found"}` |
| 422 | `id` or `relation_id` <= 0 or not an int | validation envelope |

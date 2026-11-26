# Quickstart: validate the feature

Prerequisite: stack up (`./myths up -d`).

1. `./myths test tests/domains/test_entities.py --no-cov -k "delete_relation or remove_with_reverse"` — new tests pass.
2. `./myths test` — full suite green, coverage gate holds.
3. Manual (superuser token): `POST /entities/{A}/relations` with `SIBLINGS` to B; `DELETE /entities/{A}/relations/{id}` → 204; `GET /entities/{B}/relations` no longer lists it. Repeat with `MOTHER_CHILD` and confirm only that row goes. See [contract](contracts/delete-entity-relation.md) for error codes.

# Quickstart: Validate the enum CHECK constraints

Prerequisites: stack running (`./myths up -d`). Database queries use the container's own env vars,
so no secrets are typed or read. Shorthand used below:

```sh
PSQL='docker compose exec -T db sh -c'
Q='psql -U "$POSTGRES_USER" "$POSTGRES_DB" -At -c'
```

1. **Tests (rejection + sync)**: `./myths test tests/domains/test_enum_check_constraints.py --no-cov`
   is green; before the models/migration exist it fails because invalid inserts succeed (Red).
2. **Full suite + gate**: `./myths test` → all green (≥ 276 passed), coverage ≥ 68%, no existing
   test modified (SC-005).
3. **Clean upgrade**: `./myths alembic upgrade head` succeeds on the seeded dev DB; list the
   constraints:
   `$PSQL "$Q \"select conname, pg_get_constraintdef(oid) from pg_constraint where conname like 'ck\_%' order by 1\""`
   → five rows (names in [data-model.md](data-model.md)).
4. **DB rejects invalid value (SC-001)**: attempt
   `insert into category (name) values ('myth')` via `$PSQL`; expect `violates check constraint
   "ck_category_name"`. Repeat one invalid insert per column.
5. **Down**: `./myths alembic downgrade -1` → the five constraints are gone, row counts unchanged.
6. **Up again**: `./myths alembic upgrade head` succeeds; capture
   `pg_dump -s` after steps 3 and 6 and confirm identical (SC-004). Filter the random `\restrict` / `\unrestrict` nonce lines first, e.g. `grep -v -E '^\\(un)?restrict'`; they are the only thing that differs between dumps.
7. **Abort on dirty data (SC-003)**: after step 5 (constraints absent), insert one invalid row
   (e.g. `insert into source (entity_id, source_type, title) values (1, 'PODCAST', 'x')`), run
   `./myths alembic upgrade head`; expect a single error naming `source`, `source_type`,
   `PODCAST`, and `./myths alembic current` still at the previous revision with zero constraints.
   Delete the invalid row and re-run the upgrade successfully.
8. **API smoke**: `curl -L` on `/api/v1/categories` and `/api/v1/entity-types` (without `-L` they answer 307 for the missing trailing slash) return 200 with seeded
   values.

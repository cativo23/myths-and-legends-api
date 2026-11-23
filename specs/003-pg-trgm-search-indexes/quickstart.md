# Quickstart: Validate the trigram search indexes

Prerequisites: stack running (`./myths up -d`). Database queries use the container's own env vars,
so no secrets are typed or read. Shorthand used below:

```sh
PSQL='docker compose exec -T db sh -c'
Q='psql -U "$POSTGRES_USER" "$POSTGRES_DB" -At -c'
```

(`./myths psql` is broken: it targets service `pgsql`, not `db`; noted in the ROADMAP.)

1. **Guard test (Red → Green)**: `./myths test tests/domains/test_trigram_search_indexes.py --no-cov`
   fails before the model edit (B-tree still declared) and passes after.
2. **Full suite + gate**: `./myths test` → all green (≥ 329 passed), coverage ≥ 68%, no existing
   test modified (SC-003).
3. **Black**: `uvx black --check app`.
4. **Privilege check (FR-010)**: `$PSQL "$Q \"select rolsuper from pg_roles where rolname=current_user; select trusted from pg_available_extension_versions where name='pg_trgm'\""`
   → `trusted = t`. The dev role is a superuser; in production the DB owner suffices.
5. **Baseline schema**: capture `pg_dump -s` (filter `grep -v -E '^\\(un)?restrict'`) to a scratch file.
6. **Upgrade**: `./myths alembic upgrade head`, then list indexes:
   `$PSQL "$Q \"select indexname from pg_indexes where tablename in ('entity','location') and (indexname like '%trgm' or indexname='ix_entity_description') order by 1\""`
   → four `*_trgm` rows, no `ix_entity_description`. `\dx`-equivalent:
   `$PSQL "$Q \"select extname from pg_extension\""` includes `pg_trgm`.
7. **Down**: `./myths alembic downgrade -1` → four `*_trgm` gone, `ix_entity_description` back as
   B-tree, row counts unchanged, `pg_trgm` still installed. `pg_dump -s` matches step 5 ignoring
   the extension lines (SC-004).
8. **Up again**: `./myths alembic upgrade head` succeeds with the extension already present.
9. **Index use on the seed data (forced)**: `ANALYZE entity; ANALYZE location;` then, one
   transaction per query:

   ```sql
   BEGIN;
   SET LOCAL enable_seqscan = off;
   EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
     SELECT * FROM entity
     WHERE name ILIKE '%god%' OR description ILIKE '%god%' OR origin ILIKE '%god%';
   ROLLBACK;
   ```

   Expect `BitmapOr` over three `Bitmap Index Scan` on `ix_entity_name_trgm`,
   `ix_entity_description_trgm`, `ix_entity_origin_trgm`. Repeat for
   `SELECT count(*) FROM location WHERE department ILIKE '%san%'` → `Bitmap Index Scan` on
   `ix_location_department_trgm`. (Do not use `ORDER BY id LIMIT`; the primary key wins there.)
10. **Index use without forcing (SC-001, SC-002)**: in a throwaway database (`CREATE DATABASE
    trgm_scratch`, never `myths`), build the two tables with ~80k entities and ~100k locations of
    synthetic text, create the same extension and indexes, `ANALYZE`, and EXPLAIN a term of 3+
    characters matching under 5% of rows without `enable_seqscan=off`. Record plan type and times,
    then `DROP DATABASE trgm_scratch`.
11. **Result parity (SC-003)**: for a handful of terms (including mixed case and a NULL-description
    entity), the rows returned by the search with and without the indexes (`SET LOCAL
    enable_bitmapscan = off; SET LOCAL enable_indexscan = off;`) are identical.
12. **API smoke**: `curl "http://localhost:8080/api/v1/entities/search?q=god"` and
    `curl -L "http://localhost:8080/api/v1/locations/?department=San"` return 200 with the same
    items as before.

# Research: Hardening leftovers of issue #54

## R1. Where does duplication exist today?
- Decision: extract `apply_sort` + `SortOrder` into `app/api/common/sorting.py`.
- Rationale: `getattr(Model, sort)` + `desc()/asc()` is copied in categories, entity_types, sources; countries/users/entities would add three more. Six call sites justify one helper; `id` tie-breaker (spec edge case) lives in one place.
- Alternatives: copy the pattern (rejected: duplication); generic sort dependency/factory (rejected: over-abstraction, each endpoint needs its own field `Literal` for OpenAPI).

## R2. Users and entities ordering
- Decision: `_build_query` in `CRUDBaseService` gets optional `sort`/`order` (default id, as today); `get_paginated` in the entity service gets the same.
- Rationale: users go through `get_all` → `_build_query`; no new query path.
- Alternatives: build `select(User)` inside the endpoint like categories (rejected: second copy of the same query logic).

## R3. Countries
- Decision: sort in SQL via `_build_query`/`apply_sort`; drop Python `sorted`. Remove `relations` from list and detail.
- Rationale: `Country` has no relationships (id, name, status), so `getattr(Country, r)` raised `AttributeError` (500) for every non-empty value; nothing can be loaded. Found during implementation; Carlos chose removal (YAGNI).
- Alternatives: empty allowlist returning 422 (rejected: keeps a parameter that can never work); model the relations (rejected: schema change, out of scope for #54).

## R4. Compose password
- Decision: `${VAR:?message}`; CI passes its own password (no dependency on the default). `env_file: .env` already feeds the variable.
- Verification: `POSTGRES_PASSWORD= docker compose config` must fail with the message; with a value it succeeds. A pytest cannot run it (the api container has no docker binary), so it is a step in the CI `build` job.

## R6. Null ordering
- Decision: `apply_sort` uses `.nulls_last()`. Postgres puts NULLs last on asc and first on desc, SQLite the opposite, and tests run on SQLite; explicit nulls-last makes both engines agree.

## R5. Out of scope (recorded, not done)
`datetime.utcnow()` (utils.py, health.py, entity.py), `.dict()` in api_responses.py, `Optional[X]` style, `python-jose` maintenance → noted in ROADMAP.

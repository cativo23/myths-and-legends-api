# Research: API freeze for v0.2.0

## R1. Why the default 429 ignores the app's handler

- **Finding**: `SlowAPIMiddleware` (the sync-check path) looks up the app's handler for `RateLimitExceeded` but, if that handler is a coroutine function, **falls back to slowapi's own** `_rate_limit_exceeded_handler` (`{"error": ...}`). Our `rate_limit_exception_handler` is `async def`, so it is only used for per-route limits (where FastAPI raises the exception normally).
- **Decision**: make our handler a plain `def`. One-word change; both paths then use it.
- **Alternatives**: subclass or replace the middleware (more code, more to maintain); register a second handler (does not help, the middleware picks by type); change the body to slowapi's shape (rejected by Carlos, and it would break the frontend's `detail.retry_after`).
- **Consequence**: the constitution's Layered rule says endpoints are sync `def`; a sync handler is consistent with it.

## R2. `retry_after` is always `null` today

- **Finding**: `RateLimitExceeded` has `limit` and `detail` only; the handler's `getattr(exc, "retry_after", None)` therefore always yields `None`. The frontend reads `detail.retry_after` to tell the user how long to wait, so a permanent `null` makes the unified envelope useless to it.
- **Decision**: compute it in the handler: seconds until the window of the limit that was hit resets, from the limiter's window stats for `exc.limit`, rounded up to at least 1; fall back to `null` if unavailable. The test pins that it is a positive integer.
- **Alternatives**: keep `null` and rely on a `Retry-After` header (slowapi only injects it when `headers_enabled` is on, which it is not); drop the field (breaks the decided envelope).
- **Flag**: this goes slightly beyond "unify the shape", but the shape is meaningless without it. Included as its own commit so it can be dropped in review.

## R3. Deduplicating symmetric relations

- **Finding**: `GET /entities/{id}` and `GET /entities/{id}/relations` each build the summary list with the same loop (duplicated code), from `get_relations_graph` / `get_by_entity`, both returning every row touching the entity. For a symmetric relation A–B there are two rows (A→B and B→A), so A sees both.
- **Decision**: one shared function builds the summaries and, for symmetric types, keeps only the row where the **queried entity is the origin**; if the reverse row does not exist (legacy or hand-made data) the lone row is kept regardless of direction. Both endpoints use it, which also removes the duplicated loop. Pairs are keyed by `(relation_type, related_entity_id)`.
- **Scope note**: the spec names the entity detail; `/relations` is the same data and the frontend could call either, so leaving it duplicated would reintroduce the problem. Raised in the plan so Carlos can veto.
- **Alternatives**: only dedupe the detail (inconsistent); dedupe in the query (SQL gets complicated, no benefit at this size); store one row (migration, rejected by decision).
- **Direction value**: for a deduplicated symmetric relation `direction` is `origin` from the queried entity's side, which matches what the origin row already says today.

## R4. Image credit

- **Finding**: `Entity.image_url` is a plain `String(500)`; the entity create/update schemas (`EntityBase`, `EntityUpdate`) and the read schemas share fields. Image upload lives in its own `images` domain and does not touch entity creation, so the credit is just another optional metadata column.
- **Decision**: `image_credit: String(255) NULL`, in `EntityBase` and `EntityUpdate`, exposed in `Entity` and `EntityWithRelations` (and built explicitly in `get_entity`, which constructs the response field by field). A validator strips whitespace and turns blank into `None`; explicit `""` on update clears it, omission keeps it.
- **Migration**: `add_column` nullable, no server default, no backfill; `downgrade` drops it. Verified up, down, up on PostgreSQL (constitution V). No DB-level constraint beyond the length, since blank is normalized at the boundary and existing `CHECK` patterns in this repo are for enum-like columns.
- **Alternatives**: carry the credit in `Source` (rejected by Carlos); a separate credits table (YAGNI).

## R5. `Token.expires_at`

- **Finding**: `get_token_expiry` returns `datetime.utcfromtimestamp(exp)`, a **naive** datetime, so it would serialize as `2026-11-27T10:30:00` with no offset. A browser parses that as local time, shifting the expiry by the user's UTC offset; the BFF needs this to set cookie lifetimes (roadmap 2.4).
- **Decision**: type the field `datetime` **and** return a timezone-aware UTC value (`datetime.fromtimestamp(exp, tz=timezone.utc)`), so JSON carries `+00:00`/`Z`. The OpenAPI then says `format: date-time`.
- **Impact check**: callers and tests of `get_token_expiry` and `expires_at` are listed in the tasks; any that compare to a naive `utcnow()` are updated.
- **Alternatives**: type only (leaves the local-time trap); epoch integer (a different contract than the Roadmap's `datetime`).

## R6. Docs rewrite and Fair Use

- **Finding**: stale examples live in `schemas/entity_type.py`, `schemas/entity.py` (category and entity type examples, `Anubis`), `endpoints/entities.py` (type filter) and `endpoints/entity_types.py`. The public docs description is the string in `app/main.py`; admin docs are separate (`openapi_config.py`). `version="0.2.0"` is already set in `app/main.py`.
- **Decision**: replace examples with Salvadoran ones (for instance El Cipitío, La Siguanaba, El Cadejo, La Carreta Chillona as CHARACTER; MYTH/LEGEND/TRADITION categories; `entity_type` shown as the real type values). Verification is a test that scans the generated OpenAPI JSON for the foreign-mythology words, so the cleanup cannot silently regress.
- **Fair Use**: a short section in the public description in `app/main.py` stating that content is for educational and cultural purposes, that artwork belongs to its credited artists, and how to request corrections. Wording is shown to Carlos in the PR; it is not legal advice.
- **Open for review**: whether a Salvadoran-specific example set should include real entity data. It does not: examples are illustrative strings only.

## R7. E2E tests to update (spec 007)

- `tests/e2e/test_rate_limit_boundaries.py`: replace the "JSON only" assertion for the default limit with the exact envelope; apply it to all five tests.
- `tests/e2e/test_entity_graph_journey.py` and `conftest.py` (`graph_snapshot`): symmetric relations appear once per side.
- `tests/domains/test_entities.py` and the relation tests: any that assert two rows for a symmetric pair.
- Each is changed **to the new expectation first** and seen failing for the right reason before the fix (Red), then green.

## R8. Release mechanics

- `CHANGELOG.md` has only an `[Unreleased]` section; add `## [0.2.0] - <merge date>` by moving the entries and adding the new ones.
- ROADMAP: 1.7 ✅, risks 16 to 19 closed with the decision; 2.3's block note updated to "unblocked once `v0.2.0` exists".
- The tag is created on the merge commit after Carlos confirms. Until then the frontend cannot take its snapshot from the tag.

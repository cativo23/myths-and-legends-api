# Phase 1: Backend Hardening & Admin-Ready API

**Date:** 2026-07-16
**Status:** Approved for planning

## Context

This is Phase 1 of a 3-phase effort to take myths-and-legends-api to production:

1. **Phase 1 (this spec)** — backend cleanup, new endpoints, and decisions needed before a frontend can be built against a stable contract
2. **Phase 2 (separate spec)** — a Nuxt frontend: public catalog + admin panel, themed API docs
3. **Phase 3 (separate spec)** — deploy to `space-server` (Carlos's self-hosted VPS), following the `portfolio-api` pattern

Phase 1 exists because the frontend (Phase 2) needs write endpoints and auth behavior that don't exist yet, and because several open issues affect API behavior the frontend will depend on (search quality, session length, rate limiting).

## Goals

- The admin panel (Phase 2) can fully manage every resource in the catalog — not just entities/countries/users, which is all that has CRUD today
- Public read access remains open (no API key), matching the PokeAPI model, protected by the rate limiting already in place
- Search actually works for substring queries, not just exact/prefix matches
- Admin sessions don't hard-expire after 8 days with no recovery path
- Close out the backlog of review findings from the earlier hardening pass (issues #26, #31, #54, #60, #67, #68, #69, #70)

## Non-goals

- No frontend work (Phase 2)
- No deployment work (Phase 3)
- No API key / tiered-access system — explicitly decided against (see Decisions)

## Scope

### A. Structural cleanup

- **Move `app/api/v1/entities/` → `app/api/v1/domains/entities/`** (closes #67). Purely mechanical: every domain except `entities` already lives under `domains/`. Update all import paths (`from app.api.v1.entities.X` → `from app.api.v1.domains.entities.X`) across the codebase — roughly 40+ files. No behavior change, no route path change (the `entities` router keeps the same URL prefix).
- **Add DB-level `CHECK` constraints on enum-backed columns** (closes #68): `Category.name`, `EntityType.name`, `Characteristic.type`, `EntityRelation.relation_type`, `Source.source_type`. New Alembic migration. Pydantic already validates these at the API layer; this adds a DB-level guarantee so a raw SQL insert or future admin tool can't bypass it.

### B. Write endpoints for reference data

Categories, entity-types, locations, sources currently only support `GET` (list/detail). Add `POST`/`PUT`/`DELETE` for each, matching the exact pattern already used by `entities`/`countries`:
- `Depends(get_current_active_superuser)` on every write endpoint
- Same response/error conventions (201 on create, 204 on delete, 404 on missing ID)
- Service layer already exists for all four (`CategoryService`, `EntityTypeService`, `LocationService`, `SourceService`) — they just need the endpoint + schema wiring, no new service methods beyond what `CRUDBaseService` already provides.

### C. Refresh tokens (closes #69)

Current: a single JWT access token, 8-day expiry, no way to revoke early short of rotating `SECRET_KEY` (which invalidates every token, not just one).

Add: a refresh-token flow so the admin panel doesn't need to force a full re-login every 8 days.
- New `POST /auth/refresh` endpoint: accepts a valid refresh token, returns a new access token
- Refresh tokens are longer-lived (e.g. 30 days) but single-use or rotated on each refresh (standard practice — reduces the blast radius of a leaked refresh token)
- Both access and refresh tokens get an explicit `"type"` claim (`"access"` vs `"refresh"`) so one can never be used in place of the other — this also closes a latent token-confusion gap flagged during the earlier security review
- Storage: a `refresh_tokens` table (or a single `current_refresh_token_hash` column on `User`, simpler but only supports one active session per user — needs a decision at planning time based on whether multi-device admin sessions matter) to support revocation (e.g. on password change, force-logout)

### D. Entity relations endpoint (closes #70)

`EntityRelationService.create_bidirectional()` exists, is used by `seed.py`, but has no API endpoint. Add:
- `POST /entities/{id}/relations` — body: `{destination_entity_id, relation_type}`. Calls `create_bidirectional`, which already auto-mirrors symmetric relation types (SIBLINGS/ALLIES/ENEMIES).
- Superuser-gated, matching every other write endpoint.
- Consider whether a `DELETE /entities/{id}/relations/{relation_id}` is also needed for the admin panel to remove a relation — decide at planning time based on whether Phase 2's admin UI wants this (likely yes, if relations are manageable at all, deletion should be too).

### E. Search: switch to `pg_trgm` (closes #60)

Current `ILIKE '%term%'` search across `Entity.name`/`description`/`origin` (and `Location.department`) can't use any of the existing B-tree indexes — always a sequential scan. Decided: `pg_trgm` over full-text search, because a public search box should match arbitrary substrings ("type anything"), not just whole words/stems.

- Enable the `pg_trgm` Postgres extension (migration)
- Add GIN trigram indexes on `Entity.name`, `Entity.description`, `Entity.origin`, `Location.department`
- Drop the now-redundant plain B-tree index on `Entity.description` (`ix_entity_description`, added by an earlier migration that didn't actually help this query pattern)
- No application code change needed for the query itself — `pg_trgm` makes the existing `ILIKE` pattern indexable, it doesn't require a different query shape

### F. Caching for reference-data reads (closes #26)

Categories, entity-types, sources are read-heavy, low-write-frequency (per the earlier database-optimizer review). Add an in-memory TTL cache (`fastapi-cache2`, `InMemoryBackend` — no new infra dependency, this is a single-instance deployment) on their `GET` list endpoints:
- 5–10 min TTL on categories/entity-types (effectively static, enum-backed)
- 60s TTL on sources (tied to entity edits, changes more often)
- No write-path cache invalidation needed — TTL expiry is sufficient at this write frequency and traffic level

### G. E2E tests (closes #31)

The 3 flows identified during the earlier test-master review:
1. **Full entity lifecycle with relations**: create category → entity-type → two entities → create a relation between them (now possible per item D) → fetch entity with nested `/relations` → delete one entity → verify the relation is gone
2. **Full auth lifecycle**: superuser creates a user → login → access a protected resource → password-recovery → reset-password → re-login with new password → (now also) refresh the access token (per item C) → confirm the old access token's behavior at/after expiry
3. **Rate-limit boundaries across endpoints**: confirm the general 60/min limit and the auth-specific 10/min limit are enforced independently — hammering `/login` doesn't rate-limit `/entities/`, and vice versa

### H. Remaining #54 leftovers

- `sort` parameter validation gap still open on `countries` and `users` endpoints (the earlier pagination-fix pass covered `categories`/`entity-types`/`sources`/`locations` but missed these two) — same `Literal[...]` fix
- Fix the rate-limiter docstring that overstates behavior (says a route-level limit "replaces" the default; it actually stacks additively)
- Add a test asserting `Settings()` raises `ValidationError` when `SECRET_KEY`/`POSTGRES_PASSWORD`/`FIRST_SUPERUSER_PASSWORD` are absent (still missing despite the required-secrets validator existing since earlier this session)
- Remove the weak default password fallback in `docker-compose.yml` (`POSTGRES_PASSWORD:-myths`) so it fails loudly instead of silently running with a guessable default

## Decisions

**No API key for public reads.** Researched PokeAPI directly (their docs + GitHub issues) as the explicit reference point: PokeAPI requires no key and, since 2018, has *no rate limiting at all* — relying purely on a fair-use policy and IP bans. This project already has real rate limiting (60/min general, 10/min auth) — stricter than PokeAPI's current setup. A tiered "optional key for higher limits" model was considered and rejected: its entire purpose would be inviting *more* sustained traffic onto a single-Postgres, resource-constrained VPS, which is precisely the traffic the rate limiter exists to prevent. 60/min (3,600/hr) is generous for any well-behaved integration (hobbyist bots, periodic polling, even a one-time full-catalog crawl). If a real consumer ever needs more, it's a one-line env var bump or manual IP allowlist — not a self-serve key subsystem. Action item: add a short "Fair Use" note to the public `/docs` page (no key required, please cache client-side, abusive IPs get blocked).

## Testing

- Every new endpoint (B, D) gets the same test coverage shape as existing CRUD endpoints: success, 404, 401 (no auth), 403 (non-superuser)
- Refresh-token flow (C) gets dedicated tests: issue → refresh → old-vs-new token behavior → refresh-token reuse-after-rotation rejected
- `pg_trgm` migration (E) gets a live up/down/up verification against a real Postgres, same rigor as this session's earlier migrations
- E2E tests (G) as specified above
- Full existing suite (170 tests) must continue passing throughout

## Risks / open questions for planning

- Refresh-token storage model (single-column vs dedicated table) needs a decision at plan time based on whether multi-device admin sessions matter — default assumption unless told otherwise: single active session is fine (personal project, one admin).
- Whether relation deletion (`DELETE /entities/{id}/relations/{relation_id}`) is in scope for Phase 1 or deferred to Phase 2 depends on the admin panel's actual UI needs — flag for Phase 2 spec if deferred.
- This phase is large (8 work areas). At planning time, consider whether it should execute as one big plan or be split into 2-3 executable chunks (e.g., "new endpoints + structural cleanup" as one wave, "auth + search + caching" as another, "tests + #54 leftovers" as a third) — the earlier hardening pass in this same repo used 5 parallel-but-sequenced PRs successfully; a similar shape likely fits here.

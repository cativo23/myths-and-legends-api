# Feature Specification: Cache for public reference-data reads

**Feature Branch**: `feature/cache-reference-reads` (spec directory is independent of branch name)

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "Caching of public reference-data reads (issue #26, roadmap 1.3). Cache in memory (fastapi-cache2, InMemory backend, no Redis) the 6 public GET endpoints of categories, entity-types and sources (list and detail). TTL: categories and entity-types 300 s, sources 60 s. No explicit invalidation on writes: stale data until the TTL expires is accepted (Carlos's decision). The cache key is built only from validated parameters, never from the raw query string or the DB session. 404s and errors are not cached. Keep Cache-Control and weak ETag headers; remove X-FastAPI-Cache. Endpoints stay sync `def`. The cache is initialised at app startup, does not exempt requests from rate limiting, and is cleared between tests by an autouse fixture, with no config flag. New dependency capped in requirements.in with a regenerated lock."

## Clarifications

### Session 2026-11-23

- Q: After a write on categories, entity-types or sources, accept stale data until TTL or invalidate on write? → A: Accept staleness until TTL expires (no invalidation), as the roadmap states.
- Q: Exact TTL for categories and entity-types (roadmap range 5-10 min)? → A: 300 s. Sources stays at 60 s.
- Q: Which endpoints are cached? → A: All 6 public GETs (list and detail) of categories, entity-types and sources. Error responses (404) are never cached.
- Q: How is cache memory bounded (the in-memory backend only evicts expired entries when re-read, and `page` has no upper limit)? → A: Do not cache empty pages. Together with FR-005 and parameter-only keys, entries are limited by real data. No entry cap, no custom backend.
- Q: Which cache headers are exposed? → A: `Cache-Control: max-age` and weak `ETag` stay (clients can revalidate and get 304); the `X-FastAPI-Cache` HIT/MISS header is removed so the cache state is not revealed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repeated reads of reference data skip the database (Priority: P1)

A client (the future frontend, mostly) repeatedly lists categories, entity types and sources to fill dropdowns and filters. These lists change rarely. The first request in a time window is answered from the database; later identical requests inside the window are answered from memory with the same body.

**Why this priority**: This is the point of issue #26: the most frequent reads hit data that almost never changes.

**Independent Test**: Call a cached list endpoint twice with the same parameters and confirm the second response is byte-identical while the database was queried only once (e.g. by counting queries or by changing the row between calls and still seeing the old value inside the TTL).

**Acceptance Scenarios**:

1. **Given** an empty cache, **When** a client requests `GET /categories/` twice with identical parameters, **Then** both responses are identical and only the first reaches the database.
2. **Given** a cached response, **When** the TTL elapses (300 s for categories/entity-types, 60 s for sources), **Then** the next request reaches the database and returns current data.
3. **Given** a cached category, **When** a superuser renames it, **Then** reads keep returning the old name until the TTL expires (accepted, documented staleness).
4. **Given** the detail endpoints (`GET /{id}`), **When** requested twice for an existing id, **Then** the second is served from memory.

---

### User Story 2 - The cache never mixes up or leaks responses (Priority: P1)

Each distinct request (page, size, sort, order, source type, id) gets its own cached response. A client cannot make the cache return the wrong response, and cannot grow it with junk keys.

**Why this priority**: A caching bug here silently serves wrong data to every user, and an unbounded key space is a memory exhaustion risk on a public API (Constitution II).

**Independent Test**: Request the same endpoint with different valid parameter combinations and with extra unknown query parameters, then verify each valid combination returns its own correct data and unknown parameters do not create new entries.

**Acceptance Scenarios**:

1. **Given** two requests that differ in `page`, `size`, `sort`, `order` or `source_type`, **When** both are made, **Then** each returns data matching its own parameters.
2. **Given** a request with unknown query parameters (e.g. `?foo=1`), **When** repeated with different values, **Then** all share the same cache entry as the request without them.
3. **Given** a request that fails validation (422) or an id that does not exist (404), **When** repeated, **Then** every attempt reaches validation/the database and no error response is cached.
4. **Given** the cache is shared by all callers, **When** an authenticated and an anonymous client request the same URL, **Then** both receive the same body (these endpoints do not depend on the caller).
5. **Given** a list request for a page with no items (page beyond the data), **When** repeated, **Then** every attempt reaches the database and the empty page is not cached, so the number of cache entries stays bounded by the real data.

---

### User Story 3 - Clients can revalidate and the cache keeps its limits (Priority: P2)

Cached responses carry standard HTTP cache headers so clients can cache and revalidate them. The cache does not weaken rate limiting and does not reveal internal state.

**Why this priority**: Gives clients the benefit of HTTP caching, while keeping security headers and rate limits intact.

**Independent Test**: Request a cached endpoint, read the headers, repeat with `If-None-Match` and confirm a 304; confirm `X-FastAPI-Cache` never appears; exceed the rate limit with cached requests and confirm 429.

**Acceptance Scenarios**:

1. **Given** a cached list, **When** the client sends `If-None-Match` with the previous ETag, **Then** the response is 304 with no body.
2. **Given** any cached endpoint, **When** the response is inspected, **Then** it has `Cache-Control: max-age` and `ETag` and does not have `X-FastAPI-Cache`.
3. **Given** a client exceeding the general rate limit, **When** it keeps requesting cached endpoints, **Then** it receives 429 as for any other endpoint.
4. **Given** a client sending `Cache-Control: no-cache`, **When** it requests a cached endpoint, **Then** it forces a refresh from the database; this is bounded by the rate limit (documented behaviour of the library).
5. **Given** the standard security headers, CORS headers and request id, **When** a cached response is returned, **Then** they are still present.

---

### Edge Cases

- A write (POST/PUT/DELETE) on a cached resource does not invalidate anything; data may be stale up to the TTL (60 s sources, 300 s categories/entity-types).
- Multiple application workers each keep their own memory cache; staleness windows and ETags can differ between workers.
- Cache entries are lost on restart; the first requests after a restart reach the database.
- Cache state must not persist between tests (a fresh cache is created on every application startup).
- Cache storage failure must not break the endpoint (fall back to the database).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The 6 public GET endpoints of categories, entity-types and sources (list and detail) MUST serve repeated identical requests from an in-memory cache within the TTL.
- **FR-002**: TTL MUST be 300 s for categories and entity-types and 60 s for sources.
- **FR-003**: Writes MUST NOT trigger explicit invalidation; staleness up to the TTL is accepted and documented.
- **FR-004**: The cache key MUST be derived only from the endpoint and its validated parameters (page, size, sort, order, source_type, id). Unknown query parameters, the raw query string, headers and the database session MUST NOT influence the key.
- **FR-005**: Error responses (404, 422, 5xx) MUST NOT be cached.
- **FR-006**: Cached responses MUST carry `Cache-Control: max-age` and a weak `ETag`, support 304 on `If-None-Match`, and MUST NOT carry `X-FastAPI-Cache`.
- **FR-007**: Cached endpoints MUST remain plain `def` endpoints (Constitution IV).
- **FR-008**: The cache MUST be initialised at application startup and MUST NOT require Redis or any external service.
- **FR-009**: Cached endpoints MUST remain subject to rate limiting, security headers, CORS and request id.
- **FR-010**: Memory growth of the cache MUST be bounded by the real data: list responses with no items (out-of-range pages) MUST NOT be cached, and error responses are never cached (FR-005), so the key space is limited to existing rows × valid `size`/`sort`/`order`/`source_type` values.
- **FR-011**: A cache backend failure MUST degrade to a normal database read, not an error.
- **FR-012**: The test suite MUST start every test with an empty cache, without a configuration flag (fresh cache per application startup, which each test client triggers).
- **FR-013**: The new dependency MUST be capped in `requirements.in` and the hashed lock regenerated; it MUST be compatible with the pinned FastAPI/Starlette/Pydantic and not pull Redis.
- **FR-014**: Endpoint behaviour on a cache miss (bodies, status codes, pagination envelope, error envelope) MUST be identical to today.

### Key Entities

- **Cached response**: the serialised body of a GET of a reference resource, keyed by endpoint plus validated parameters, with an expiry time.
- **Reference resources**: categories, entity types, sources. Public to read, superuser-only to write.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A second identical request inside the TTL triggers zero database queries on the 6 cached endpoints.
- **SC-002**: After a write, the old data is visible for at most the TTL (60 s / 300 s) and current data after it.
- **SC-003**: Across all valid and invalid parameter variations, no cached response is ever returned for a request with different validated parameters, and error responses are never cached.
- **SC-004**: Cache memory is bounded as defined in FR-010 under a hostile client varying `page`, `size` and query strings.
- **SC-005**: The full existing test suite passes unchanged (no cross-test contamination) with coverage not below the 68% gate.
- **SC-006**: Rate limiting still returns 429 on cached endpoints once the limit is exceeded.

## Assumptions

- Reference data changes rarely and is edited by a few superusers, so minutes of staleness are acceptable.
- A single worker is the current deployment; per-worker caches are acceptable.
- Entities, countries, locations and users endpoints are out of scope (their data is larger, filtered, or user-related).
- A shared/distributed cache (Redis) is out of scope.
- The library is sync-compatible: it runs the project's sync `def` endpoints in a threadpool.

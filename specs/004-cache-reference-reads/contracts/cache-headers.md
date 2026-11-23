# Contract: cached reference reads

Applies to: `GET /api/v1/categories/`, `/categories/{id}`, `/entity-types/`, `/entity-types/{id}`,
`/sources/`, `/sources/{id}`.

| Aspect | Contract |
|---|---|
| Body and status | Identical to pre-cache behavior (same `Page` envelope, same `HTTPException` errors) |
| `Cache-Control` | `max-age=<seconds>`: full TTL on a miss, remaining TTL on a hit (300 / 60 max) |
| `ETag` | weak validator; `If-None-Match` equal to it returns `304` with empty body |
| `X-FastAPI-Cache` | never present |
| Errors | 404 / 422 never cached; no cache headers guaranteed on them |
| Empty list page | served from DB each time, not cached |
| Writes | no invalidation; data may be stale up to the TTL |
| Request `Cache-Control: no-cache` / `no-store` | bypass the cache (subject to rate limiting) |
| Rate limiting, CORS, security headers, request id | unchanged |

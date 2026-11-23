# Research: Cache for public reference-data reads

## R1. fastapi-cache2 compatibility

- Decision: `fastapi-cache2>=0.2.2,<0.3`; add `jinja2>=3.1,<4` as a direct dependency.
- Finding: `fastapi_cache.coder` imports `starlette.templating`, which raises `ImportError` without
  `jinja2`. fastapi-cache2 does not declare jinja2. Without the pin the app would fail at import.
- Finding: resolves with FastAPI 0.135 / Starlette 1.x / Pydantic 2.14; only new transitive package
  is `pendulum` (+ jinja2 / markupsafe). `redis` is an optional extra and is not installed.
- Rationale: caps follow the repo convention (floor + next breaking). The lock is regenerated with
  the documented `uv pip compile` command using the existing `requirements.txt` as preference so
  unrelated pins do not move.

## R2. Sync endpoints

- Decision: keep endpoints as `def`.
- Finding: the decorator's inner function is `async`; for a sync function it calls
  `run_in_threadpool(func, ...)`. The decorator augments the signature with injected `Request` and
  `Response` parameters, so FastAPI still resolves `Depends(get_db)` and query params normally.
  Misses return the same `Page` object as today; hits return a decoded dict validated by the
  existing `response_model`.

## R3. Cache key

- Decision: custom `key_builder` set globally in `FastAPICache.init`. Key =
  `namespace : module.function : sorted JSON of primitive validated kwargs`.
- Finding: the default builder hashes `str(kwargs)`, which includes the `Session` repr (memory
  address), so every request would be a miss. Raw query string is never read, so unknown params
  cannot create keys; invalid params fail validation (422) before the decorator runs.
- Primitive filter: keep `str|int|float|bool|None|Enum` values (Enum by `.value`); everything else
  (the `Session`) is ignored by type, not by name.

## R4. Memory growth

- Finding: `InMemoryBackend` keeps a class-level dict and only deletes an expired key when that key
  is read again; unread expired keys stay forever.
- Decision (Carlos): do not cache empty pages. Subclass `InMemoryBackend` with an instance-level
  store and a `set()` that skips JSON bodies with `"items": []`. Errors never reach `set()` (the
  exception propagates). Key space = existing rows × valid size/sort/order/type values.
- Alternatives: entry cap with eviction (more code), accept growth (hostile `page=N`).

## R5. Headers

- Library sets `Cache-Control: max-age=<ttl>`, weak `ETag` (`W/<hash(body)>`) and `X-FastAPI-Cache`
  on both miss and hit, and returns 304 when `If-None-Match` equals the ETag.
- Decision (Carlos): keep the first two, remove `X-FastAPI-Cache`. The status header name cannot be
  disabled via `init`, so `SecurityHeadersMiddleware` deletes it (it already owns outgoing headers).
- Note: `hash()` of bytes is salted per process, so ETags differ across restarts/workers.
- Note: request `Cache-Control: no-cache` bypasses and refreshes; `no-store` bypasses. Bounded by
  the rate limit; accepted.

## R6. Lifecycle and test isolation

- Decision: add `lifespan` to `app/main.py` calling `init_cache()` which does
  `FastAPICache.reset()` then `FastAPICache.init(ReferenceCacheBackend(), ...)`.
- `FastAPICache.init` is a no-op if already initialised, hence the explicit reset. Each test's
  `TestClient` context runs the lifespan, so every test starts with a fresh, empty backend; no
  conftest change and no config flag. A test proves it. Tests that skip the lifespan fail loudly
  (library asserts "You must call init first"), not silently.

## R7. Rate limiter and middleware order

- `SlowAPIMiddleware` resolves the route handler by name; the decorator uses `functools.wraps`, so
  default limits still apply to cached endpoints. Verified by a test (429 after the limit).
- Middleware order is unchanged; the cache sits inside the route, so CORS, security headers and
  request id still wrap every response, cached or not.

## R8. Cache hit and DB session

- `Depends(get_db)` still opens a session on a hit (no query is issued). Accepted; avoiding it would
  need restructuring dependencies and is out of scope.

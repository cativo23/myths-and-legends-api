# Research: End-to-end user-flow tests

## Decision 1: Reuse the in-process fixtures, no new DB infrastructure

- **Decision**: Use `client`/`db` from `tests/conftest.py` (SQLite file per test, outer transaction rolled back).
- **Rationale**: Chosen with Carlos. Meets "separate test database" of #31 already; CI runs the same way. A Postgres fixture would add infrastructure with no known Postgres-only bug to catch.
- **Alternatives**: Real Postgres engine (CI has the service but the suite never uses it); HTTP against the live stack (needs CI to start compose).

## Decision 2: Marker applied centrally

- **Decision**: Register `e2e` in `pytest.ini` (required by `--strict-markers`) and apply it in `tests/e2e/conftest.py` with `pytest_collection_modifyitems` for items under that directory.
- **Rationale**: One place, impossible to forget on a new test; `-m e2e` runs only these, `-m "not e2e"` excludes them.
- **Alternatives**: `pytestmark` in each module (three places to keep in sync); per-test decorators.

## Decision 3: Rate-limit boundary tests

- **Facts (read from code)**: default limit is `RATE_LIMIT_PER_MINUTE` (60), applied to every route by `SlowAPIMiddleware`; recover and reset also carry `RATE_LIMIT_AUTH_PER_MINUTE` (10) per route; refresh and logout only have the default. Limiter state is reset before each test by an autouse fixture, and login/categories 429s are already tested.
- **Decision**: For recover and reset, send `RATE_LIMIT_AUTH_PER_MINUTE` calls (all non-429), then assert the next is 429 with a JSON body. For refresh and logout, send `RATE_LIMIT_PER_MINUTE` calls then assert the next is 429. Cheap requests are used (non-existent email; invalid token; unauthenticated logout) because the limiter counts requests whatever their outcome; the loops only need the status to be "not 429".
- **Rationale**: Boundary is exact and limits come from settings, so changing a setting does not break tests.
- **Risk**: slowapi per-route limits are keyed per endpoint, so recover and reset do not share the strict budget; each test uses only one endpoint so this does not matter.

## Decision 4: Refresh-token identity risk

- **Facts**: `create_refresh_token` adds a random `jti`, so two refresh tokens for the same user in the same second are distinct; rotation and reuse tests are deterministic.
- **Decision**: No sleeps or time mocking needed.

## Decision 5: Behavior asserted for reuse and one-session

- **Facts (read from `auth.py`)**: reuse of a rotated refresh token returns 401 ("already used") without touching stored state, so the newer session still works. Login overwrites the stored refresh hash, so an earlier session's refresh token is rejected with 401.
- **Decision**: The auth journey asserts exactly this.

## Decision 6: Duplication boundary

- **Decision**: Tests in `tests/domains/` stay untouched. E2E tests assert only chained behavior (output of step N is visible in step N+1), the one-session rule, and the four missing 429s. Existing per-step edge cases (malformed or expired tokens, non-positive ids, 401/403 per endpoint) are not repeated, except US1 scenario 6 which checks a regular user changes nothing in the graph.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - TBD (set the date when the tag is created)

API frozen for the frontend: the contract changes below were made before the
first consumer, so they are not versioned separately.

### Added

- Optional `image_credit` on entities (max 255 characters, trimmed, blank means
  none) to credit the artist of the image. Accepted on create and update (an update
  that omits it keeps it, an empty one clears it) and returned by list and detail.
- A "Fair Use" section in the public API documentation (`/docs`).
- In-memory response cache (`fastapi-cache2`, no Redis) on the public `GET` endpoints
  of categories, entity types and sources (list and detail): 300 s for categories
  and entity types, 60 s for sources (#26). Writes do not invalidate it, so data can
  be stale until the TTL expires. Responses carry `Cache-Control: max-age` and a weak
  `ETag` (`If-None-Match` returns `304`); `X-FastAPI-Cache` is stripped. Keys use only
  validated parameters, and errors and empty pages are never cached. The cache is
  per worker and starts empty on every restart. New dependencies: `fastapi-cache2`
  and `jinja2` (a hidden import of fastapi-cache2).
- Database-level `CHECK` constraints on the enum-like columns `category.name`,
  `entity_type.name`, `characteristic.type`, `entity_relation.relation_type` and
  `source.source_type` (migration `ce04f762989d`), so raw SQL or bulk imports can
  no longer store values outside the allowed sets (#68). The upgrade aborts with
  a message listing table, column and offending values if existing rows violate
  them, and never modifies data. Adding or renaming an enum value now needs a
  migration that updates the constraint (a test fails otherwise).
- Write endpoints for the entities domain (all superuser-gated):
  - `POST`, `PUT`, `DELETE` for categories (`/api/v1/categories`)
  - `POST`, `PUT`, `DELETE` for entity types (`/api/v1/entity-types`)
  - `POST`, `PUT`, `DELETE` for locations (`/api/v1/locations`)
  - `POST`, `PUT`, `DELETE` for sources (`/api/v1/sources`)
  - `POST /api/v1/entities/{id}/relations` to create relations between entities,
    with symmetric relation types (SIBLINGS, ALLIES, ENEMIES) automatically
    creating the reverse relation
- Refresh-token auth flow:
  - `POST /api/v1/auth/refresh` exchanges a refresh token for a new access +
    refresh pair; refresh tokens are single use (rotated on every call, with an
    atomic compare-and-swap so concurrent calls cannot both succeed)
  - `POST /api/v1/auth/logout` revokes the user's refresh token (the access
    token stays valid until it expires)
  - `REFRESH_TOKEN_EXPIRE_DAYS` setting (default 30)
- 404 responses on `POST /api/v1/locations` and `POST /api/v1/sources` when the
  given `entity_id` does not reference an existing entity, instead of an
  unhandled 500

### Changed

- **Contract:** every `429` now answers `{"detail": {"message", "type":
  "rate_limit_exceeded", "retry_after"}}`. The default limit used to answer
  `{"error": ...}` because slowapi replaces a coroutine handler with its own, and
  `retry_after` was always `null`; it is now the number of seconds until the window
  resets.
- **Contract:** `GET /entities/{id}` and `GET /entities/{id}/relations` list a
  symmetric relation (siblings, allies, enemies) once, from the queried entity's
  point of view (`direction: origin`). Storage is unchanged: two rows per pair, and
  deleting either removes both.
- **Contract:** `Token.expires_at` (login and refresh) is a `date-time` in the
  OpenAPI document and is returned as UTC with an offset; it used to be untyped and
  naive, so browsers read it as local time.
- Descriptions, examples and the README describe the Salvadoran catalog (types
  `CHARACTER`, `PLACE`, `OBJECT`, `GROUP`, `EVENT`; categories `MYTH`, `LEGEND`,
  `TRADITION`) instead of Egyptian, Greek and Norse mythologies. A test scans the
  OpenAPI so the old wording cannot return.
- `POST /api/v1/auth/login` now also returns a `refresh_token`. One refresh
  token per user is stored (hashed), so a new login replaces the previous
  session's refresh token.
- Password hashing now calls `bcrypt` directly instead of the unmaintained
  `passlib` (and its import-time monkeypatch of `bcrypt`). Existing stored
  hashes keep verifying with no migration; passwords are still truncated to
  72 bytes. A malformed stored hash now fails verification instead of raising,
  and passwords containing a NUL byte are accepted instead of rejected.
- Direct dependencies in `requirements.txt` now have upper bounds (next
  breaking release), so a fresh install cannot jump to an untested major.
- Dependencies are now locked: `requirements.in` holds the direct dependencies
  and their caps, and `requirements.txt` is a hashed lock generated from it
  (`uv pip compile --universal`). Docker and CI install it with
  `--require-hashes`, and a new CI `lock` job fails when the lock is stale, so
  local, CI and container installs resolve identical versions.
- `./myths test` now runs the real test runner (`test.py`) instead of failing,
  and as the `myths` user so coverage artifacts are no longer root-owned.
- **Breaking:** `entity_id` is now a required field when creating a `Location`
  or a `Source` (previously optional). Omitting it now returns a `422`
  instead of raising an unhandled `500` on the database foreign key
  constraint.

### Fixed

- 409 response on duplicate category/entity-type name instead of an unhandled
  `IntegrityError`
- Database URLs use the explicit `postgresql+psycopg2` driver (app settings and
  `alembic/env.py`). SQLAlchemy 2.1 defaults plain `postgresql` to psycopg3,
  which this project does not ship; this broke CI.

### Database Migrations

- `25d308c4dfa0`: adds nullable `entity.image_credit` (`VARCHAR(255)`). Written by
  hand because `alembic revision --autogenerate` proposes dropping the trigram and
  location indexes (it cannot see the GIN indexes of `b0ac58dc2755`).
- `0f2ce4cae13f`: adds nullable `user.hashed_refresh_token` column

## [0.1.0] - 2026-04-02

### Added

- Public and admin OpenAPI documentation (`/docs` and `/admin/docs`)
- OAuth2 authentication schema for Swagger/ReDoc
- Domain-driven project structure
- Comprehensive API descriptions, examples, and response schemas
- Rate limiting middleware
- Security headers middleware (CSP, X-Frame-Options, etc.)
- Request ID middleware for tracing
- Entity management (entities, categories, entity_types, locations, sources)
- Country and character management
- User authentication with JWT tokens
- Health check endpoints
- Image upload and serving functionality
- PostgreSQL database with Alembic migrations
- Docker and Docker Compose configuration
- CI/CD pipeline with GitHub Actions

### Changed

- Refactored from flat structure to domain-driven architecture
- Updated Pydantic schemas to v2
- Improved error handling with custom exception classes

### Fixed

- Fixed images router prefix duplication
- Fixed Pydantic deprecation warnings
- Fixed CI lint and test failures

### Database Migrations

- `4758804d863e_add_entities_tables.py` - Add entities, categories, entity_types, locations, sources tables
- `d077d52b1166_remove_characters_table.py` - Remove deprecated characters table
- `d15753a0d7f5_add_characters.py` - Add characters with new structure
- `53cafc_add_unique_fields_on_character_s_name.py` - Add unique constraints

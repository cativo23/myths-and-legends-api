# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI REST API, "The API of Myths and Legends", that manages mythological entities (characters, creatures, places, objects), their relations, and countries. PostgreSQL + SQLAlchemy 2.0 ORM, service-layer architecture, JWT auth with refresh tokens.

## Workflow

- Spec-Driven Development with GitHub Spec Kit: `/speckit-specify → clarify → plan → tasks → analyze → implement → converge`. New feature specs live in `specs/NNN-*/`; `docs/superpowers/` is historical.
- Every plan must pass the Constitution Check against `.specify/memory/constitution.md` (TDD, security-first, minimalism, sync `def` + `Session`, `HTTPException` error envelope, conventional commits).
- Roadmap and session order: `docs/ROADMAP.md`. Branches are `type/short-description`; `develop` requires 1 review and green CI.

## Architecture Structure

- **app/main.py**: FastAPI entry point (CORS, rate limiting, pagination, middleware)
- **app/api/v1/router.py**: Aggregates all v1 routers
- **app/api/v1/domains/<domain>/**: one folder per domain, each with `endpoints/`, `services/`, and where applicable `models/`, `schemas/`
  - `auth` (login, refresh, logout, password reset), `users`, `countries`, `health`, `home`, `images`
  - `entities` (entities, categories, entity types, locations, sources, relations; also `enums.py` and `seed.py`)
- **app/api/v1/shared/**: shared dependencies (`deps/dependencies.py`: DB session, current user) and enums
- **app/api/common/**: base CRUD service, exception handlers, response helpers, middleware (rate limiter, security headers, request ID), pagination
- **app/core/**: `config.py` (Pydantic `BaseSettings`), `security.py` (JWT, hashing), logging and OpenAPI config
- **app/db/**: session and base SQLAlchemy class with automatic table naming
- **alembic/**: migrations
- **tests/**: pytest suite; `tests/domains/` mirrors the domains

## Development Commands

### Application
- `./myths up` / `./myths up -d` - Start (foreground / background)
- `./myths stop`, `./myths restart`, `./myths ps`
- `./myths shell` / `./myths bash` - Container shell; `./myths root-shell` as root
- `./myths python ...` - Run Python in the container
- `./myths build --no-cache` - Rebuild containers

### Database
- `./myths alembic revision --autogenerate -m "message"` - New migration
- `./myths alembic upgrade head` - Apply migrations
- `./myths psql` - PostgreSQL shell

### Testing
The stack must be running (`./myths up -d`). Run the suite in the container:

- `./myths python test.py tests --no-cov -p no:cacheprovider` - Full suite
- `./myths python test.py tests/test_cors.py --no-cov -p no:cacheprovider` - One file

`--no-cov` avoids a `htmlcov/` permission error (the directory is created by root in the container). Note: `./myths test` is currently broken (it runs `python test` instead of `python test.py`).

## Key Technologies

Versions are capped in `requirements.txt` (floor and next-breaking ceiling); check it rather than trusting this list.

- FastAPI 0.135 / Starlette 1.0, Pydantic 2.x, pydantic-settings
- SQLAlchemy 2.0 with an explicit `postgresql+psycopg2` driver (2.1 defaults to psycopg3 and broke CI)
- Alembic, PostgreSQL 15
- python-jose (JWT), passlib/bcrypt, slowapi (rate limiting)
- fastapi-pagination, Docker Compose

## Common Patterns

- Services extend `CRUDBaseService` for standard CRUD; endpoints and services are sync (`def` + `Session`), not async
- DB sessions via `Depends(get_db)`; auth via `get_current_user` / superuser dependencies
- Errors are raised as `HTTPException` (standard envelope); duplicate names on write endpoints return `409`
- Writes on reference data and entities are superuser-gated; reads are public
- Auth: access token plus a single-use, rotated refresh token stored hashed on the user (one session per user); logout revokes the refresh token only
- Image upload is integrated into entity create/update

## Environment Configuration

Settings come from environment variables or `.env` via `app/core/config.py`. `SECRET_KEY`, `POSTGRES_PASSWORD` and `FIRST_SUPERUSER_PASSWORD` are required; startup fails without them. Never commit `.env`. `BACKEND_CORS_ORIGINS` varies per developer, so tests must not hardcode origins.

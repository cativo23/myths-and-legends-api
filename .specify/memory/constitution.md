# Myths and Legends API Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

Every behavior change follows Red → Green → Refactor.

- A failing test that describes the desired behavior MUST exist, and be seen failing for the
  right reason, before any implementation code is written.
- Each test MUST cover one behavior, not one function, and its name MUST describe that behavior
  (e.g. `should_reject_expired_tokens`).
- A bug fix MUST start with a test that reproduces the bug.
- External dependencies MUST be wrapped and the wrapper mocked; third-party code MUST NOT be
  mocked directly.

Rationale: the API is the contract for a future frontend; regressions must be caught by tests,
not by consumers.

### II. Security-First

- Secrets (keys, tokens, passwords) MUST NOT appear in code, logs, tests, or error messages.
- All external input (request bodies, query params, headers, files, env vars) MUST be validated
  at the system boundary.
- Error responses MUST help the developer debug without leaking stack traces, file paths, or
  internal IDs.
- Every write endpoint MUST depend on `get_current_active_superuser`; public access is
  read-only.
- Defaults MUST be secure: required secrets have no fallback value, HTTPS over HTTP, and
  parameterized queries over string concatenation.
- Access is least-privilege: services and containers MUST NOT run as root or hold broader
  permissions than they need.

Rationale: this API is publicly exposed; its write surface must never be reachable by
anonymous or non-admin users.

### III. Minimalism (YAGNI)

- The smallest viable solution MUST be chosen first; complexity is added only when the simple
  approach demonstrably fails.
- Abstractions, configuration, and feature flags for hypothetical future needs MUST NOT be
  added. Three similar lines are preferred over a premature abstraction.
- Work that exceeds the scope of the current spec MUST be raised with the maintainer before it
  is done.
- Unused code MUST be deleted; no backwards-compatibility shims for internal code.
- Validation and error handling live at system boundaries; internal code is trusted.

Rationale: a single-maintainer project survives on small, reviewable, reversible changes.

### IV. Layered Architecture & Synchronous Conventions

- Code follows endpoints → services → models/schemas. Business logic lives in services that
  extend `CRUDBaseService`; endpoints stay thin.
- Endpoints MUST be plain `def` (not `async def`) because the project uses a synchronous
  SQLAlchemy `Session`.
- Database sessions MUST be injected via `Annotated[Session, Depends(get_db)]`.
- Errors MUST be raised as `HTTPException(status_code, detail)`; no second error envelope is
  introduced for individual resources.
- New resources follow the established domain layout under `app/api/v1/domains/`.

Rationale: consistency lets every new endpoint be written and reviewed by pattern.

### V. Verified Database Migrations

- Every schema change MUST ship as an Alembic migration with a working `downgrade`.
- Each migration MUST be verified up → down → up against a real PostgreSQL instance, not a
  mock or SQLite.
- Application-level validation (Pydantic) MUST be backed by DB-level guarantees (constraints,
  indexes) where the data model depends on them.

Rationale: migrations are the only change that cannot be trivially rolled back in production.

## Technical Constraints

- Stack: FastAPI, SQLAlchemy ORM, Pydantic, PostgreSQL, Alembic, Docker Compose,
  fastapi-pagination. Exact versions are governed by `requirements.txt`, not by this document.
- The full test suite MUST be green before a branch is merged; no merge with failing or
  skipped-to-pass tests.
- Public reads stay keyless and are protected by the existing rate limiting; an API-key tier is
  out of scope unless this constitution is amended.
- Configuration is read through `app/core/config.py` from environment variables; required
  secrets MUST fail startup when absent.

## Development Workflow

- Spec-Driven Development with Spec Kit: one feature per cycle
  (`specify → clarify → plan → tasks → analyze → implement → converge`).
- One work session maps to one part of `docs/ROADMAP.md`. A session ends with a handoff
  summary (done, pending, decisions, next prompt) before a new session starts.
- Commits use conventional commits `type(scope): description` (feat, fix, docs, refactor,
  test, chore), focus on why rather than what, and hold one concern each.
- Branches are named `type/short-description`; PR titles are imperative and under 70
  characters.
- Every PR diff is self-reviewed as if written by someone else before it is opened; non-obvious
  decisions carry a one-line comment explaining why.
- TODOs carry context: `TODO(name): reason — ticket/date`.

## Governance

This constitution supersedes other project practices. Amendments require a documented change
to this file via `/speckit-constitution`, a version bump, and a note on any specs or plans that
must be revisited.

Versioning follows semantic versioning: MAJOR for removed or redefined principles, MINOR for
new principles or materially expanded guidance, PATCH for clarifications. Every plan produced
by `/speckit-plan` MUST pass a Constitution Check against these principles; any justified
violation MUST be recorded in the plan's complexity-tracking section. Compliance is verified
during self-review and PR review. Runtime guidance for the AI assistant lives in `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-11-18 | **Last Amended**: 2026-11-18

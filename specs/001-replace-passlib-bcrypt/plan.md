# Implementation Plan: Replace passlib with direct bcrypt

**Branch**: `chore/tooling-reproducibility` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-replace-passlib-bcrypt/spec.md`

## Summary

Replace passlib's `CryptContext` with direct calls to the `bcrypt` library inside the two public
functions of `app/core/security.py`, delete the import-time monkeypatch, and drop passlib from
`requirements.txt` (bcrypt bounded to `>=5,<6`). Compatibility is proven by characterization
tests written first against the current implementation (fixture hashes, 72-byte boundary,
unicode), then kept green through the swap. One intentional delta: `verify_password` fails
closed (returns `False`) on a malformed stored hash instead of raising.

## Technical Context

**Language/Version**: Python 3.10 (Docker), CI matrix 3.10 / 3.11 / 3.12

**Primary Dependencies**: `bcrypt` 5.x (already installed transitively via `passlib[bcrypt]`); passlib removed

**Storage**: PostgreSQL; `users.hashed_password` is an opaque string, schema unchanged, no migration

**Testing**: pytest via `./myths test`; new tests in `tests/test_security.py`

**Target Platform**: Linux container

**Project Type**: web-service (FastAPI)

**Performance Goals**: unchanged; cost factor 12 preserved (measured from current hashes: `$2b$12$`)

**Constraints**: stored hashes must verify without rehash; hashes written after the change must verify under the previous implementation (rollback safety)

**Scale/Scope**: one module (`app/core/security.py`), one requirements line, tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Note |
|---|---|---|
| I. Test-First | PASS | Characterization tests (fixture hashes, boundary cases) committed and green on the old code first; failing tests added for the new behaviors (fail-closed, no import-time patching) before the swap |
| II. Security-First | PASS | Fail-closed verification; no secrets in tests (fixtures hash throwaway dummy passwords); no error detail leaks |
| III. Minimalism | PASS | No wrapper class, no config knob for rounds, no rehash-on-login, no `__init__` abstraction; two functions plus one tiny byte-prep helper |
| IV. Layered / sync | PASS | No endpoint, service, or signature changes |
| V. Migrations | N/A | No schema change |

No violations; Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-replace-passlib-bcrypt/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md             # created by /speckit-tasks
```

(`contracts/` omitted on purpose: no external interface changes.)

### Source Code (repository root)

```text
app/core/security.py        # swap implementation, delete monkeypatch
requirements.txt            # passlib[bcrypt] -> bcrypt>=5,<6
tests/test_security.py      # characterization + new behavior tests
```

**Structure Decision**: single existing module; no new files in `app/`.

## Design

```python
# app/core/security.py (sketch, not final code)
_BCRYPT_ROUNDS = 12          # matches existing hashes; do not tune here
_BCRYPT_MAX_BYTES = 72       # bcrypt ignores the rest; truncate explicitly (bcrypt 5 raises otherwise)

def _to_bcrypt_input(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_input(password), bcrypt.gensalt(_BCRYPT_ROUNDS)).decode("ascii")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_to_bcrypt_input(plain_password), hashed_password.encode("utf-8"))
    except ValueError:       # malformed stored hash: fail closed
        return False
```

Open verification points (resolved by tests, not assumptions): `$2y$` hashes verify (passlib
accepted them); NUL byte handling (measured during implementation: bcrypt 5 hashes and verifies it correctly, so no rejection code is added; this differs from passlib, which raised).

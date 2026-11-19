# Quickstart: Validate the passlib → bcrypt swap

Prerequisites: stack running (`./myths up -d`).

1. **Before the change** (baseline): `./myths test tests/test_security.py --no-cov` is green,
   including the fixture-hash characterization tests.
2. **After the change**: the same command is green with no test edits to the characterization cases.
3. **Full suite + coverage gate**: `./myths test` → 254+ passed, coverage ≥ 68%.
4. **Dependency check**: `./myths python -m pip show passlib` reports "not found" after rebuilding
   (`./myths build`); `./myths python -c "import app.core.security"` succeeds.
5. **Rollback safety (SC-003, one-off)**: generate a hash with the new code, verify it with
   `git stash`-ed old code (or the fixture-generating script on the old commit); both agree.
6. **Login smoke**: seeded superuser logs in via `POST /api/v1/auth/login` → 200.

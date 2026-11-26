# Quickstart: End-to-end user-flow tests

## Prerequisites

Stack running: `./myths up -d`. Do not run test commands in parallel in the same container.

## Validate

1. Only the E2E tests, no coverage gate:
   `./myths test tests/e2e --no-cov`
   Expected: all pass.
2. Marker selection works (and `--strict-markers` accepts it):
   `./myths test -m e2e --no-cov` runs only `tests/e2e`; `./myths test -m "not e2e" --no-cov` skips them.
3. Order independence: run one module alone, e.g. `./myths test tests/e2e/test_rate_limit_boundaries.py --no-cov`, then confirm a different module still passes right after (no limiter leakage).
4. Full suite with coverage: `./myths test`
   Expected: green, coverage at or above the previous 85.71% and the 68% gate.
5. Formatting: `uvx black --check app` (unchanged; do not format `tests/`).

## Red check (Test-First adaptation)

For each new assertion, temporarily break the behavior it protects, see the test fail for the right reason, then restore. Examples: stop overwriting the stored refresh hash on login (one-session test); delete only the forward row on symmetric delete (graph test); raise `RATE_LIMIT_AUTH_PER_MINUTE` in the test run (boundary test).

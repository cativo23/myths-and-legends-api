# Quickstart: validation

Prereq: `./myths up -d`.

1. Sorting/validation: `./myths test tests/test_sorting.py tests/domains/test_countries.py tests/domains/test_users.py tests/domains/test_entities.py --no-cov`
2. Refactor safety: `./myths test tests/domains/test_categories.py tests/domains/test_entity_types.py tests/domains/test_sources.py --no-cov`
3. Compose: `POSTGRES_PASSWORD= docker compose config` fails with the "POSTGRES_PASSWORD is required" message; `POSTGRES_PASSWORD=x docker compose config` succeeds (also enforced by the CI `build` job).
4. Full suite: `./myths test` (coverage gate 68%); `uvx black --check app`.
5. Manual: `GET /api/v1/countries?sort=__class__` → 422.

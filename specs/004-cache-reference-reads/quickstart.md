# Quickstart: validating the cache

Prerequisites: `./myths up -d`.

1. Tests: `./myths test tests/test_cache_reference_reads.py --no-cov`, then `./myths test` (coverage gate 68%, suite green).
2. Lock: `uv pip compile requirements.in --universal --python-version 3.10 --generate-hashes -o requirements.txt` leaves no diff; CI job `lock` green. `black --check app` via `uvx black --check app`.
3. Manual (stack up):
   - `curl -si localhost:8000/api/v1/categories/ | grep -iE 'cache-control|etag|x-fastapi'` shows `Cache-Control` and `ETag`, no `X-FastAPI-Cache`.
   - Repeat with `-H 'If-None-Match: <etag>'` gives `304`.
   - Rename a category as superuser: the list shows the old name until the TTL passes.
   - `?page=99999` twice: both hit the DB (empty page not cached).

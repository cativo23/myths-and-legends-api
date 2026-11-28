# Quickstart: validating the v0.2.0 freeze

Prerequisite: the stack is running (`./myths up -d`).

## Automated

```bash
./myths test tests/e2e --no-cov          # journeys with the new 429 and one-line relations
./myths test tests/domains --no-cov       # entity credit, relations, token
./myths test                              # full suite, coverage gate must hold
```

## Migration (PostgreSQL)

```bash
./myths alembic upgrade head
./myths alembic downgrade -1
./myths alembic upgrade head
./myths psql -c "\d entity"               # image_credit varchar(255), nullable
```

## By hand

1. **429**: send 61 requests to `GET /api/v1/categories/`, then 11 `POST /api/v1/auth/login` with a bad password. Both 429 bodies are `{"detail": {...}}` with a positive `retry_after`.
2. **Relations**: create a SIBLINGS relation A-B as superuser, then `GET /api/v1/entities/{A}` and `{B}`: each lists it once.
3. **Credit**: `POST /api/v1/entities/` with `"image_credit": "  Ana Perez  "` returns `"Ana Perez"`; `PUT` omitting it keeps it; `PUT` with `""` clears it.
4. **Token**: `POST /api/v1/auth/login`; `expires_at` ends in `Z` or `+00:00`.
5. **Docs**: open `/docs`; the Fair Use section is present; the OpenAPI JSON contains no Egyptian, Greek, Norse, Aztec or Japanese.

## After merge (needs Carlos's confirmation)

```bash
git tag -a v0.2.0 <merge-commit> -m "v0.2.0: API frozen for the frontend"
git push origin v0.2.0
```

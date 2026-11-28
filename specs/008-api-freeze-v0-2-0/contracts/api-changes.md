# Contract changes (v0.1.0 to v0.2.0)

All changes are visible in the OpenAPI document that the frontend snapshots from the `v0.2.0` tag.

## 429 Too Many Requests (every route)

```json
{"detail": {"message": "Rate limit exceeded. 10 per 1 minute", "type": "rate_limit_exceeded", "retry_after": 42}}
```

- Before: per-route limits used this shape; the default limit used `{"error": "Rate limit exceeded: 60 per 1 minute"}`.
- `retry_after` was always `null`; now a positive integer of seconds (falls back to `null` only if the window cannot be read).

## GET /api/v1/entities/{id} and GET /api/v1/entities/{id}/relations

- `relations[]` (and the `/relations` list) contain one item per symmetric pair, seen from the queried entity: `direction` is `origin`, `related_entity_*` is the other end.
- Directed relations are unchanged. A relation's `id` is that of the row shown (the queried entity's origin row for symmetric pairs).
- `DELETE /entities/{id}/relations/{relation_id}` unchanged: deleting either row of a symmetric pair removes both.

## Entity: new optional field `image_credit`

- `POST /entities`, `PUT /entities/{id}`: optional string, at most 255 characters.
- `GET /entities`, `GET /entities/{id}`: `"image_credit": string | null`.

## Token (login and refresh)

- `expires_at`: `{"type": "string", "format": "date-time"}`; value like `2026-11-27T18:30:00Z` (UTC, with offset).

## Documentation

- `/docs` description and every example describe the Salvadoran catalog (types CHARACTER, PLACE, OBJECT, GROUP, EVENT; categories MYTH, LEGEND, TRADITION); a "Fair Use" section is added.

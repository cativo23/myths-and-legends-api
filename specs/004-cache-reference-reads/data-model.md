# Data Model: Cache for public reference-data reads

No database change.

## Cache entry (in memory, per worker)

| Field | Description |
|---|---|
| key | `<prefix>:<namespace>:<module.function>:<sorted JSON of validated params>` |
| value | JSON bytes of the response body |
| expiry | now + TTL (300 s categories / entity-types, 60 s sources) |

Rules: only successful responses; list responses with `items == []` are not stored; no user or
header data in the key; store lives in the backend instance, replaced on every application startup.

Keyed parameters: list endpoints `page, size, sort, order` (+ `source_type` on sources); detail
endpoints `id`.

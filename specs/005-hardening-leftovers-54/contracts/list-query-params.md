# Contract: list query parameters (changes only)

| Endpoint | Param | Before | After |
|---|---|---|---|
| GET /countries | sort | any string | enum name\|id (422 otherwise) |
| GET /countries, GET /countries/{id} | relations | any string | comma list of entities\|locations, max 100 chars (422 otherwise) |
| GET /countries, /users, /entities | order | any string / ignored | enum asc\|desc (422 otherwise) |
| GET /users | sort | accepted, ignored | enum id\|email\|full_name, applied |
| GET /entities | sort | accepted, ignored | enum id\|name\|created_at, applied |

Errors keep the project's standard `HTTPException` envelope (422 from request validation). Unchanged: categories, entity-types, sources.

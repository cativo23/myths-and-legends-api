# Data Model

No schema change and no migration. Sort fields available per list (all are existing indexed or primary columns):

| Endpoint | `sort` allowed | Default | Tie-breaker |
|---|---|---|---|
| GET /countries | name, id | name | id |
| GET /users | id, email, full_name | email | id |
| GET /entities | id, name, created_at | name | id |

`order`: asc, desc (default asc). Countries `relations`: entities, locations.

# Data Model: Replace passlib with direct bcrypt

No entities change. `users.hashed_password` remains an opaque bcrypt string (`$2b$12$` + 53
chars). No Alembic migration. Existing rows verify as-is (FR-001).

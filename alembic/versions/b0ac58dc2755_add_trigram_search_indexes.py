"""add trigram search indexes

Revision ID: b0ac58dc2755
Revises: ce04f762989d
Create Date: 2026-11-23 07:44:38.762375

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0ac58dc2755'
down_revision = 'ce04f762989d'
branch_labels = None
depends_on = None


# (table, column, index name). One GIN trigram index per column that is searched
# with ILIKE '%term%': a B-tree cannot serve a leading wildcard. All three entity
# columns are needed together, because the OR in EntityService.search() only uses
# an index when every branch has one.
# Declared only here, never on the models: SQLite (create_all in the test suite)
# has no gin_trgm_ops. Index options stay at defaults; fastupdate=off was measured
# ~6x slower on inserts.
TRIGRAM_INDEXES = [
    ('entity', 'name', 'ix_entity_name_trgm'),
    ('entity', 'description', 'ix_entity_description_trgm'),
    ('entity', 'origin', 'ix_entity_origin_trgm'),
    ('location', 'department', 'ix_location_department_trgm'),
]


def upgrade():
    # pg_trgm is a trusted extension in PostgreSQL 13+, so the database owner can
    # install it without superuser. IF NOT EXISTS keeps up -> down -> up idempotent.
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    for table, column, name in TRIGRAM_INDEXES:
        op.create_index(
            name,
            table,
            [column],
            postgresql_using='gin',
            postgresql_ops={column: 'gin_trgm_ops'},
        )
    # Dropped last so description is never left without any index mid-upgrade.
    op.drop_index(op.f('ix_entity_description'), table_name='entity')


def downgrade():
    op.create_index(
        op.f('ix_entity_description'), 'entity', ['description'], unique=False
    )
    for table, _, name in reversed(TRIGRAM_INDEXES):
        op.drop_index(name, table_name=table)
    # pg_trgm is deliberately left installed: dropping it would fail if anything
    # else uses it, and the indexes above are this migration's own state.

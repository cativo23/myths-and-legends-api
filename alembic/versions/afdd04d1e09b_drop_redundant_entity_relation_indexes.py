"""drop redundant entity_relation indexes

Revision ID: afdd04d1e09b
Revises: bd728d1bc3f7
Create Date: 2026-07-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afdd04d1e09b'
down_revision = 'bd728d1bc3f7'
branch_labels = None
depends_on = None


def upgrade():
    # entity_relation had two indexes per column: the auto-generated
    # ix_entity_relation_entity_origin_id/ix_entity_relation_entity_destination_id
    # (from `index=True` on the mapped_column) duplicated the named
    # ix_entity_relation_origin/ix_entity_relation_destination indexes below.
    # Postgres only ever uses one of two identical indexes per column, so the
    # duplicates were pure write amplification. Keep the named ones, drop these.
    op.drop_index(
        op.f('ix_entity_relation_entity_origin_id'), table_name='entity_relation'
    )
    op.drop_index(
        op.f('ix_entity_relation_entity_destination_id'), table_name='entity_relation'
    )


def downgrade():
    op.create_index(
        op.f('ix_entity_relation_entity_destination_id'),
        'entity_relation',
        ['entity_destination_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_entity_relation_entity_origin_id'),
        'entity_relation',
        ['entity_origin_id'],
        unique=False,
    )

"""add index on entity description column

Revision ID: bd728d1bc3f7
Revises: d077d52b1166
Create Date: 2026-04-04 01:10:07.400379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd728d1bc3f7'
down_revision = 'd077d52b1166'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_entity_description'), 'entity', ['description'], unique=False)
    op.create_index(op.f('ix_location_municipality'), 'location', ['municipality'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_location_municipality'), table_name='location')
    op.drop_index(op.f('ix_entity_description'), table_name='entity')
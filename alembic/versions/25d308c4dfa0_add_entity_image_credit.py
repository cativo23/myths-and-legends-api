"""add entity image credit

Revision ID: 25d308c4dfa0
Revises: b0ac58dc2755
Create Date: 2026-11-28 06:10:38.763178

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25d308c4dfa0'
down_revision = 'b0ac58dc2755'
branch_labels = None
depends_on = None


# Hand-trimmed on purpose: `alembic --autogenerate` also proposes dropping the
# trigram and location indexes, because it cannot see the GIN/opclass indexes
# created in b0ac58dc2755. Only the new column belongs here.
def upgrade():
    op.add_column(
        'entity', sa.Column('image_credit', sa.String(length=255), nullable=True)
    )


def downgrade():
    op.drop_column('entity', 'image_credit')

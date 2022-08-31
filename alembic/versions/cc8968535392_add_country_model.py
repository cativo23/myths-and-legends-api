"""Add Country model

Revision ID: cc8968535392
Revises: 9c3a946eb9fe
Create Date: 2022-08-21 07:09:22.225749

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc8968535392'
down_revision = '9c3a946eb9fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('country',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('status', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_country_id'), 'country', ['id'], unique=False)
    op.create_index(op.f('ix_country_name'), 'country', ['name'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_country_name'), table_name='country')
    op.drop_index(op.f('ix_country_id'), table_name='country')
    op.drop_table('country')
    # ### end Alembic commands ###
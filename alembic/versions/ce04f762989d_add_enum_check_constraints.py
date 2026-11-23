"""add enum check constraints

Revision ID: ce04f762989d
Revises: 0f2ce4cae13f
Create Date: 2026-11-23 06:46:23.227234

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce04f762989d'
down_revision = '0f2ce4cae13f'
branch_labels = None
depends_on = None

# (table, column, constraint name, allowed values).
# Deliberately a frozen copy, NOT imported from app/.../enums.py: a migration is
# history and must not change meaning when an enum is edited later. A test
# (tests/domains/test_enum_check_constraints.py) fails if this drifts from the enums.
CHECKS = [
    ('category', 'name', 'ck_category_name', ('MYTH', 'LEGEND', 'TRADITION')),
    (
        'entity_type',
        'name',
        'ck_entity_type_name',
        ('CHARACTER', 'PLACE', 'OBJECT', 'GROUP', 'EVENT'),
    ),
    (
        'characteristic',
        'type',
        'ck_characteristic_type',
        ('PHYSICAL', 'APPEARANCE', 'ABILITY', 'WEAKNESS'),
    ),
    (
        'entity_relation',
        'relation_type',
        'ck_entity_relation_relation_type',
        (
            'MOTHER_CHILD',
            'FATHER_CHILD',
            'SIBLINGS',
            'GUARDIAN_PLACE',
            'ENEMIES',
            'ALLIES',
        ),
    ),
    (
        'source',
        'source_type',
        'ck_source_source_type',
        ('BOOK', 'ORAL_TRADITION', 'WEB', 'DOCUMENT'),
    ),
]


def upgrade():
    # Adding a CHECK to a table with violating rows would fail anyway, but with
    # a generic message naming only the constraint. Scan first, across all
    # columns, so the maintainer sees every offender at once. Data is never
    # modified: silently repairing reference data would be worse than refusing.
    bind = op.get_bind()
    offenders = []
    for table, column, _, allowed in CHECKS:
        col = sa.column(column, sa.String)
        query = (
            sa.select(col)
            .select_from(sa.table(table))
            .where(col.not_in(allowed))
            .distinct()
        )
        values = sorted(row[0] for row in bind.execute(query))
        if values:
            offenders.append(f"{table}.{column}: {values!r}")

    if offenders:
        raise RuntimeError(
            "Cannot add enum CHECK constraints; rows hold values outside the "
            "allowed sets (" + "; ".join(offenders) + "). Fix or remove those "
            "rows, then re-run the upgrade. No data was changed."
        )

    for table, column, name, allowed in CHECKS:
        op.create_check_constraint(
            name, table, sa.column(column, sa.String).in_(allowed)
        )


def downgrade():
    for table, _, name, _ in reversed(CHECKS):
        op.drop_constraint(name, table, type_='check')

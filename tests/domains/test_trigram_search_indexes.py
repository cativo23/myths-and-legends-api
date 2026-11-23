"""
Guards for the trigram search indexes (issue #60).

The GIN `gin_trgm_ops` indexes exist only in the Alembic migration: SQLite,
which the test suite builds with `create_all`, has no trigram operator class.
Their behavior (planner uses them, up -> down -> up) is verified by hand on real
PostgreSQL; see specs/003-pg-trgm-search-indexes/quickstart.md.

What SQLite *can* observe is the model metadata, which is what is guarded here.
"""

from app.api.v1.domains.entities.models.entity import Entity
from app.api.v1.domains.entities.models.location import Location


def _single_column_indexes(table, column_name):
    return [
        index
        for index in table.indexes
        if [column.name for column in index.columns] == [column_name]
    ]


def test_should_not_declare_a_btree_index_on_entity_description():
    # A B-tree cannot serve ILIKE '%term%', so it only adds write cost. The
    # migration drops it; the model must not recreate it on fresh databases.
    assert _single_column_indexes(Entity.__table__, "description") == []


def test_should_not_declare_trigram_indexes_on_models():
    # `create_all` also builds model-declared indexes on SQLite, where
    # gin_trgm_ops does not exist: declaring them here would break the suite.
    declared = [
        index.name
        for table in (Entity.__table__, Location.__table__)
        for index in table.indexes
    ]
    assert [name for name in declared if name.endswith("_trgm")] == []

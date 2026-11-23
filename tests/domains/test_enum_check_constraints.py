"""
The database itself must refuse values outside the enum-like columns' allowed
sets (issue #68). Rows are written with Core `insert()`/`update()` and plain
strings on purpose: that mimics raw SQL, a bulk import or a manual `psql` fix,
which bypass both Pydantic and the Python enums.

Every case gets its own `db` fixture (fresh database), so a failed statement
can never contaminate the next case.
"""

import pytest
from sqlalchemy import insert, update
from sqlalchemy.exc import IntegrityError

from app.api.v1.domains.entities.enums import (
    CategoryName,
    CharacteristicType,
    EntityTypeName,
    RelationType,
    SourceType,
)
from app.api.v1.domains.entities.models.category import Category
from app.api.v1.domains.entities.models.characteristic import Characteristic
from app.api.v1.domains.entities.models.entity import Entity
from app.api.v1.domains.entities.models.entity_relation import EntityRelation
from app.api.v1.domains.entities.models.entity_type import EntityType
from app.api.v1.domains.entities.models.source import Source


def _entity_ids(db, count):
    """Create `count` entities sharing one category/type; return their ids."""
    category = Category(name=CategoryName.MYTH, description="parent")
    entity_type = EntityType(name=EntityTypeName.CHARACTER, description="parent")
    db.add_all([category, entity_type])
    db.flush()
    entities = [
        Entity(
            name=f"parent-{i}", category_id=category.id, entity_type_id=entity_type.id
        )
        for i in range(count)
    ]
    db.add_all(entities)
    db.flush()
    return [e.id for e in entities]


def _no_extras(db):
    return {}


def _characteristic_extras(db):
    return {"entity_id": _entity_ids(db, 1)[0], "description": "x"}


def _relation_extras(db):
    origin, destination = _entity_ids(db, 2)
    return {"entity_origin_id": origin, "entity_destination_id": destination}


def _source_extras(db):
    return {"entity_id": _entity_ids(db, 1)[0], "title": "x"}


# (model, column, enum class, builder for the other required columns)
COLUMNS = [
    (Category, "name", CategoryName, _no_extras),
    (EntityType, "name", EntityTypeName, _no_extras),
    (Characteristic, "type", CharacteristicType, _characteristic_extras),
    (EntityRelation, "relation_type", RelationType, _relation_extras),
    (Source, "source_type", SourceType, _source_extras),
]

# Invalid values are derived from a valid one so near-misses are covered too.
INVALID_KINDS = {
    "unknown": lambda valid: "INVALID",
    "lowercase": lambda valid: valid.lower(),
    "trailing_space": lambda valid: valid + " ",
    "empty": lambda valid: "",
}


def _label(model, column):
    return f"{model.__tablename__}.{column}"


ACCEPT_CASES = [
    pytest.param(
        model,
        column,
        builder,
        member.value,
        id=f"{_label(model, column)}-{member.value}",
    )
    for model, column, enum_cls, builder in COLUMNS
    for member in enum_cls
]

REJECT_CASES = [
    pytest.param(
        model,
        column,
        builder,
        make(next(iter(enum_cls)).value),
        id=f"{_label(model, column)}-{kind}",
    )
    for model, column, enum_cls, builder in COLUMNS
    for kind, make in INVALID_KINDS.items()
]

COLUMN_CASES = [
    pytest.param(model, column, enum_cls, builder, id=_label(model, column))
    for model, column, enum_cls, builder in COLUMNS
]


@pytest.mark.parametrize("model,column,builder,value", ACCEPT_CASES)
def test_should_accept_every_allowed_value(db, model, column, builder, value):
    values = {column: value, **builder(db)}

    db.execute(insert(model.__table__).values(**values))
    db.flush()


@pytest.mark.parametrize("model,column,builder,value", REJECT_CASES)
def test_should_reject_value_outside_allowed_set(db, model, column, builder, value):
    values = {column: value, **builder(db)}

    with pytest.raises(IntegrityError):
        db.execute(insert(model.__table__).values(**values))


@pytest.mark.parametrize("model,column,enum_cls,builder", COLUMN_CASES)
def test_should_reject_update_to_value_outside_allowed_set(
    db, model, column, enum_cls, builder
):
    valid = next(iter(enum_cls)).value
    result = db.execute(
        insert(model.__table__).values(**{column: valid}, **builder(db))
    )
    row_id = result.inserted_primary_key[0]

    with pytest.raises(IntegrityError):
        db.execute(
            update(model.__table__)
            .where(model.__table__.c.id == row_id)
            .values(**{column: "INVALID"})
        )


@pytest.mark.parametrize("model,column,enum_cls,builder", COLUMN_CASES)
def test_should_reject_null_in_enum_column(db, model, column, enum_cls, builder):
    # NULL is refused by the existing NOT NULL, not by the new CHECK (a CHECK
    # passes on NULL); this pins the spec edge case so neither guard regresses.
    with pytest.raises(IntegrityError):
        db.execute(insert(model.__table__).values(**{column: None}, **builder(db)))

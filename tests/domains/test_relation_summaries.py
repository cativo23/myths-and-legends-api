"""Edge cases of the one-line-per-relationship summary (spec 008, FR-003/004).

Plain objects stand in for stored rows: the builder only reads their fields,
and these shapes (lone rows, self relations) are hard to create through the API.
"""
from types import SimpleNamespace

from app.api.v1.domains.entities.services import relation
from app.api.v1.domains.entities.models.entity_relation import RelationType


def _entity(entity_id: int, name: str):
    return SimpleNamespace(id=entity_id, name=name)


def _row(row_id, origin, destination, relation_type):
    return SimpleNamespace(
        id=row_id,
        entity_origin_id=origin.id,
        entity_destination_id=destination.id,
        entity_origin=origin,
        entity_destination=destination,
        relation_type=relation_type,
        description=None,
    )


ISIS, OSIRIS, SET = _entity(1, "Isis"), _entity(2, "Osiris"), _entity(3, "Set")


def test_should_keep_a_lone_symmetric_row_that_points_at_the_viewer():
    rows = [_row(10, OSIRIS, ISIS, RelationType.SIBLINGS)]

    result = relation.summarize_for_entity(rows, entity_id=ISIS.id)

    assert [(s.related_entity_id, s.direction) for s in result] == [(2, "destination")]


def test_should_prefer_the_origin_row_whichever_order_the_rows_come_in():
    forward = _row(10, ISIS, OSIRIS, RelationType.SIBLINGS)
    reverse = _row(11, OSIRIS, ISIS, RelationType.SIBLINGS)

    for rows in ([forward, reverse], [reverse, forward]):
        result = relation.summarize_for_entity(rows, entity_id=ISIS.id)

        assert [(s.id, s.direction) for s in result] == [(10, "origin")]


def test_should_keep_two_symmetric_types_between_the_same_pair():
    rows = [
        _row(10, ISIS, OSIRIS, RelationType.SIBLINGS),
        _row(11, OSIRIS, ISIS, RelationType.SIBLINGS),
        _row(12, ISIS, OSIRIS, RelationType.ALLIES),
        _row(13, OSIRIS, ISIS, RelationType.ALLIES),
    ]

    result = relation.summarize_for_entity(rows, entity_id=ISIS.id)

    assert sorted(s.relation_type for s in result) == ["ALLIES", "SIBLINGS"]


def test_should_not_merge_directed_relations_to_different_entities():
    rows = [
        _row(10, ISIS, OSIRIS, RelationType.MOTHER_CHILD),
        _row(11, ISIS, SET, RelationType.MOTHER_CHILD),
    ]

    result = relation.summarize_for_entity(rows, entity_id=ISIS.id)

    assert len(result) == 2


def test_should_collapse_the_two_rows_of_a_self_relation():
    rows = [
        _row(10, ISIS, ISIS, RelationType.ALLIES),
        _row(11, ISIS, ISIS, RelationType.ALLIES),
    ]

    result = relation.summarize_for_entity(rows, entity_id=ISIS.id)

    assert len(result) == 1

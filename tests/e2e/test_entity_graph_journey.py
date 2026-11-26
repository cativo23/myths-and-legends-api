"""
E2E journey: a superuser builds a small mythology graph, reads it back from
every side, and prunes it. Per-endpoint edge cases (404s, 422s, 401/403 per
route) live in tests/domains/test_entities.py and are not repeated here.
"""
from fastapi.testclient import TestClient

from tests.e2e.conftest import graph_snapshot

# A symmetric relation is stored as two rows (forward and reverse), and an
# entity's details list every row where it is origin or destination, so each
# end of SIBLINGS shows it twice: once per direction. Directed relations show
# once per end.
EXPECTED_GRAPH = {
    "Isis": {
        ("SIBLINGS", "Osiris", "origin"),
        ("SIBLINGS", "Osiris", "destination"),
        ("MOTHER_CHILD", "Horus", "origin"),
        ("GUARDIAN_PLACE", "Temple of Philae", "origin"),
    },
    "Osiris": {
        ("SIBLINGS", "Isis", "origin"),
        ("SIBLINGS", "Isis", "destination"),
        ("FATHER_CHILD", "Horus", "origin"),
    },
    "Horus": {
        ("FATHER_CHILD", "Osiris", "destination"),
        ("MOTHER_CHILD", "Isis", "destination"),
    },
    "Temple of Philae": {("GUARDIAN_PLACE", "Isis", "destination")},
}


def _delete_relation(
    client: TestClient, headers: dict, entity_id: int, relation_id: int
):
    return client.delete(
        f"/api/v1/entities/{entity_id}/relations/{relation_id}", headers=headers
    )


def test_should_build_read_and_prune_a_relation_graph(
    client: TestClient, graph: dict
):
    # Reference data and entities created by the journey are readable and linked.
    category = client.get(f"/api/v1/categories/{graph['category']['id']}")
    entity_type = client.get(f"/api/v1/entity-types/{graph['entity_type']['id']}")
    assert category.status_code == 200 and category.json()["name"] == "MYTH"
    assert entity_type.status_code == 200 and entity_type.json()["name"] == "CHARACTER"
    for name, entity_id in graph["ids"].items():
        details = client.get(f"/api/v1/entities/{entity_id}").json()
        assert details["name"] == name
        assert details["category_id"] == graph["category"]["id"]
        assert details["entity_type_id"] == graph["entity_type"]["id"]

    # Each entity sees exactly its own edges: the symmetric relation on both
    # ends, each directed one once on each end with the right direction.
    assert graph_snapshot(client, graph["ids"]) == EXPECTED_GRAPH

    # The two rows of the symmetric relation have different ids and both ends
    # list the same pair.
    def sibling_ids(name: str) -> set[int]:
        listing = client.get(f"/api/v1/entities/{graph['ids'][name]}/relations").json()
        return {r["id"] for r in listing if r["relation_type"] == "SIBLINGS"}

    assert len(sibling_ids("Isis")) == 2
    assert sibling_ids("Isis") == sibling_ids("Osiris")


def test_should_remove_only_the_deleted_relation_from_the_graph(
    client: TestClient, graph: dict, superuser_headers: dict
):
    ids = graph["ids"]

    # Deleting the symmetric relation removes both rows, from either end.
    sibling_id = graph["relations"]["siblings"]["id"]
    assert _delete_relation(client, superuser_headers, ids["Isis"], sibling_id).status_code == 204

    after_symmetric = graph_snapshot(client, ids)
    assert after_symmetric["Isis"] == {
        ("MOTHER_CHILD", "Horus", "origin"),
        ("GUARDIAN_PLACE", "Temple of Philae", "origin"),
    }
    assert after_symmetric["Osiris"] == {("FATHER_CHILD", "Horus", "origin")}
    assert after_symmetric["Horus"] == EXPECTED_GRAPH["Horus"]
    assert after_symmetric["Temple of Philae"] == EXPECTED_GRAPH["Temple of Philae"]

    # Deleting a directed relation removes only that row.
    father_id = graph["relations"]["father"]["id"]
    assert _delete_relation(client, superuser_headers, ids["Osiris"], father_id).status_code == 204

    after_directed = graph_snapshot(client, ids)
    assert after_directed["Osiris"] == set()
    assert after_directed["Horus"] == {("MOTHER_CHILD", "Isis", "destination")}
    assert after_directed["Isis"] == after_symmetric["Isis"]
    assert after_directed["Temple of Philae"] == EXPECTED_GRAPH["Temple of Philae"]


def test_should_leave_the_graph_untouched_when_a_regular_user_tries_to_write(
    client: TestClient, graph: dict, auth_headers: dict
):
    before = graph_snapshot(client, graph["ids"])
    ids = graph["ids"]

    create_entity = client.post(
        "/api/v1/entities/",
        json={
            "name": "Intruder",
            "category_id": graph["category"]["id"],
            "entity_type_id": graph["entity_type"]["id"],
        },
        headers=auth_headers,
    )
    create_relation = client.post(
        f"/api/v1/entities/{ids['Horus']}/relations",
        json={"entity_destination_id": ids["Isis"], "relation_type": "ALLIES"},
        headers=auth_headers,
    )
    delete_relation = _delete_relation(
        client, auth_headers, ids["Isis"], graph["relations"]["siblings"]["id"]
    )

    assert [
        create_entity.status_code,
        create_relation.status_code,
        delete_relation.status_code,
    ] == [403, 403, 403]
    assert graph_snapshot(client, ids) == before
    assert client.get("/api/v1/entities/").json()["total"] == len(ids)

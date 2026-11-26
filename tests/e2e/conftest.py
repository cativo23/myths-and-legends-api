"""
Fixtures and collection hooks shared by the end-to-end journeys.

Journeys go through HTTP only, on the per-test SQLite database from
tests/conftest.py. Anything a journey needs to *verify* is read back through
the API, never straight from the session.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

E2E_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items):
    """Mark every test under tests/e2e as `e2e` in one place, so a new test
    cannot forget it and `-m e2e` / `-m "not e2e"` always agree."""
    for item in items:
        if E2E_DIR in Path(str(item.fspath)).parents:
            item.add_marker(pytest.mark.e2e)


def _create(client: TestClient, url: str, headers: dict, body: dict) -> dict:
    response = client.post(url, json=body, headers=headers)
    assert response.status_code == 201, f"POST {url} -> {response.status_code}"
    return response.json()


def graph_snapshot(client: TestClient, entity_ids: dict[str, int]) -> dict:
    """What each entity shows in its details: {name: {(type, related, direction)}}.

    Row ids are left out on purpose: symmetric relations have a different id on
    each side, and the journeys compare the shape of the graph, not its keys.
    """
    snapshot = {}
    for name, entity_id in entity_ids.items():
        response = client.get(f"/api/v1/entities/{entity_id}")
        assert response.status_code == 200
        snapshot[name] = {
            (r["relation_type"], r["related_entity_name"], r["direction"])
            for r in response.json()["relations"]
        }
    return snapshot


@pytest.fixture
def graph(client: TestClient, superuser_headers: dict) -> dict:
    """A small Egyptian graph built as a superuser through the API.

    Edges: Isis-Osiris SIBLINGS (symmetric, 2 rows); Osiris->Horus FATHER_CHILD,
    Isis->Horus MOTHER_CHILD, Isis->Temple GUARDIAN_PLACE (directed, 1 row each).
    """
    category = _create(
        client,
        "/api/v1/categories/",
        superuser_headers,
        {"name": "MYTH", "description": "E2E category"},
    )
    entity_type = _create(
        client,
        "/api/v1/entity-types/",
        superuser_headers,
        {"name": "CHARACTER", "description": "E2E type"},
    )
    entities = {
        name: _create(
            client,
            "/api/v1/entities/",
            superuser_headers,
            {
                "name": name,
                "category_id": category["id"],
                "entity_type_id": entity_type["id"],
            },
        )
        for name in ("Isis", "Osiris", "Horus", "Temple of Philae")
    }

    def relate(origin: str, destination: str, relation_type: str) -> dict:
        return _create(
            client,
            f"/api/v1/entities/{entities[origin]['id']}/relations",
            superuser_headers,
            {
                "entity_destination_id": entities[destination]["id"],
                "relation_type": relation_type,
            },
        )

    relations = {
        "siblings": relate("Isis", "Osiris", "SIBLINGS"),
        "father": relate("Osiris", "Horus", "FATHER_CHILD"),
        "mother": relate("Isis", "Horus", "MOTHER_CHILD"),
        "guardian": relate("Isis", "Temple of Philae", "GUARDIAN_PLACE"),
    }
    return {
        "category": category,
        "entity_type": entity_type,
        "entities": entities,
        "ids": {name: e["id"] for name, e in entities.items()},
        "relations": relations,
    }

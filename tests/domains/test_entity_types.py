"""
Tests for Entity Types domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.entities.models.entity_type import EntityType
from app.api.v1.domains.entities.enums import EntityTypeName


class TestEntityTypesEndpoints:
    """Integration tests for Entity Types endpoints."""

    def test_list_entity_types_empty(self, client: TestClient):
        """Test listing entity types when database is empty."""
        response = client.get("/api/v1/entity-types/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_entity_types(self, client: TestClient, db: Session):
        """Test listing all entity types."""
        entity_types = [
            EntityType(
                name=EntityTypeName.CHARACTER, description="Mythological characters"
            ),
            EntityType(
                name=EntityTypeName.PLACE, description="Mythological places"
            ),
            EntityType(
                name=EntityTypeName.OBJECT, description="Mythological objects"
            ),
        ]
        db.add_all(entity_types)
        db.commit()

        response = client.get("/api/v1/entity-types/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_entity_types_sorted_by_name_asc(
        self, client: TestClient, db: Session
    ):
        """Test that entity types are sorted by name ascending by default."""
        entity_types = [
            EntityType(name=EntityTypeName.OBJECT, description="Objects"),
            EntityType(name=EntityTypeName.CHARACTER, description="Characters"),
            EntityType(name=EntityTypeName.PLACE, description="Places"),
        ]
        db.add_all(entity_types)
        db.commit()

        response = client.get("/api/v1/entity-types/")
        assert response.status_code == 200
        data = response.json()
        names = [e["name"] for e in data["items"]]
        assert names == sorted(names)

    def test_list_entity_types_sorted_desc(self, client: TestClient, db: Session):
        """Test listing entity types sorted descending."""
        entity_types = [
            EntityType(name=EntityTypeName.CHARACTER, description="Characters"),
            EntityType(name=EntityTypeName.PLACE, description="Places"),
        ]
        db.add_all(entity_types)
        db.commit()

        response = client.get("/api/v1/entity-types/?order=desc")
        assert response.status_code == 200
        data = response.json()
        names = [e["name"] for e in data["items"]]
        assert names == sorted(names, reverse=True)

    def test_list_entity_types_invalid_sort_field_rejected(self, client: TestClient):
        """Test that an invalid sort field is rejected with a 422, rather than
        silently falling back to id like the old, unvalidated implementation."""
        response = client.get("/api/v1/entity-types/?sort=not_a_real_field")
        assert response.status_code == 422

    def test_list_entity_types_invalid_order_value_rejected(self, client: TestClient):
        """Test that an invalid order value is rejected with a 422, rather
        than silently falling back to ascending."""
        response = client.get("/api/v1/entity-types/?order=sideways")
        assert response.status_code == 422

    def test_get_entity_type_by_id(self, client: TestClient, db: Session):
        """Test getting an entity type by ID."""
        entity_type = EntityType(
            name=EntityTypeName.CHARACTER, description="Mythological characters"
        )
        db.add(entity_type)
        db.commit()

        response = client.get(f"/api/v1/entity-types/{entity_type.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CHARACTER"
        assert data["description"] == "Mythological characters"
        assert "id" in data
        assert "entity_count" in data

    def test_get_entity_type_not_found(self, client: TestClient):
        """Test getting a non-existent entity type."""
        response = client.get("/api/v1/entity-types/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_entity_type_response_schema(self, client: TestClient, db: Session):
        """Test that entity type response matches expected schema."""
        entity_type = EntityType(
            name=EntityTypeName.GROUP, description="Mythological groups"
        )
        db.add(entity_type)
        db.commit()

        response = client.get(f"/api/v1/entity-types/{entity_type.id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "entity_count" in data

    def test_create_entity_type(self, client: TestClient, superuser_headers: dict):
        """Test creating an entity type as superuser."""
        response = client.post(
            "/api/v1/entity-types/",
            json={"name": "EVENT", "description": "Norse mythology"},
            headers=superuser_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "EVENT"
        assert "id" in data

    def test_create_entity_type_without_auth(self, client: TestClient):
        """Test creating an entity type without auth returns 401."""
        response = client.post(
            "/api/v1/entity-types/",
            json={"name": "EVENT", "description": "test"},
        )
        assert response.status_code == 401

    def test_create_entity_type_as_regular_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating an entity type as non-superuser returns 403."""
        response = client.post(
            "/api/v1/entity-types/",
            json={"name": "EVENT", "description": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_entity_type(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test updating an entity type as superuser."""
        entity_type = EntityType(
            name=EntityTypeName.CHARACTER, description="Original description"
        )
        db.add(entity_type)
        db.commit()

        response = client.put(
            f"/api/v1/entity-types/{entity_type.id}",
            json={"description": "Updated description"},
            headers=superuser_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["name"] == "CHARACTER"

    def test_update_entity_type_without_auth(self, client: TestClient, db: Session):
        """Test updating an entity type without authentication returns 401."""
        entity_type = EntityType(
            name=EntityTypeName.CHARACTER, description="Original description"
        )
        db.add(entity_type)
        db.commit()

        response = client.put(
            f"/api/v1/entity-types/{entity_type.id}",
            json={"description": "Updated description"},
        )
        assert response.status_code == 401

    def test_update_entity_type_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test updating an entity type as non-superuser returns 403."""
        entity_type = EntityType(
            name=EntityTypeName.CHARACTER, description="Original description"
        )
        db.add(entity_type)
        db.commit()

        response = client.put(
            f"/api/v1/entity-types/{entity_type.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_entity_type_not_found(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test updating a non-existent entity type returns 404."""
        response = client.put(
            "/api/v1/entity-types/99999",
            json={"description": "test"},
            headers=superuser_headers,
        )
        assert response.status_code == 404

    def test_delete_entity_type(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test deleting an entity type as superuser."""
        entity_type = EntityType(name=EntityTypeName.PLACE, description="test")
        db.add(entity_type)
        db.commit()
        entity_type_id = entity_type.id

        response = client.delete(
            f"/api/v1/entity-types/{entity_type_id}", headers=superuser_headers
        )
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/entity-types/{entity_type_id}")
        assert get_response.status_code == 404

    def test_delete_entity_type_without_auth(self, client: TestClient, db: Session):
        """Test deleting an entity type without authentication returns 401."""
        entity_type = EntityType(name=EntityTypeName.PLACE, description="test")
        db.add(entity_type)
        db.commit()

        response = client.delete(f"/api/v1/entity-types/{entity_type.id}")
        assert response.status_code == 401

    def test_delete_entity_type_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test deleting an entity type as non-superuser returns 403."""
        entity_type = EntityType(name=EntityTypeName.PLACE, description="test")
        db.add(entity_type)
        db.commit()

        response = client.delete(
            f"/api/v1/entity-types/{entity_type.id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_delete_entity_type_not_found(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test deleting a non-existent entity type returns 404."""
        response = client.delete(
            "/api/v1/entity-types/99999", headers=superuser_headers
        )
        assert response.status_code == 404

    def test_create_entity_type_duplicate_name_returns_409(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test creating an entity type with a name that already exists
        returns 409, not an unhandled IntegrityError (EntityType.name is
        unique)."""
        db.add(EntityType(name=EntityTypeName.CHARACTER, description="Existing"))
        db.commit()

        response = client.post(
            "/api/v1/entity-types/",
            json={"name": "CHARACTER", "description": "Duplicate"},
            headers=superuser_headers,
        )
        assert response.status_code == 409

    def test_create_entity_type_invalid_name_rejected(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test creating an entity type with a name outside the
        EntityTypeName enum is rejected with 422, not silently accepted."""
        response = client.post(
            "/api/v1/entity-types/",
            json={"name": "NOT_A_REAL_TYPE", "description": "test"},
            headers=superuser_headers,
        )
        assert response.status_code == 422

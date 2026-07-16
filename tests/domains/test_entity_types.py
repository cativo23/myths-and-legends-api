"""
Tests for Entity Types domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.enums import EntityTypeName


class TestEntityTypesEndpoints:
    """Integration tests for Entity Types endpoints."""

    def test_list_entity_types_empty(self, client: TestClient):
        """Test listing entity types when database is empty."""
        response = client.get("/api/v1/entity-types/")
        assert response.status_code == 200
        data = response.json()
        assert data == []

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
        assert len(data) == 3

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
        names = [e["name"] for e in data]
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
        names = [e["name"] for e in data]
        assert names == sorted(names, reverse=True)

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

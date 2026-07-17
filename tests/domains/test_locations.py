"""
Tests for Locations domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.entities.models.location import Location
from app.api.v1.domains.entities.models.category import Category
from app.api.v1.domains.entities.models.entity import Entity
from app.api.v1.domains.entities.models.entity_type import EntityType
from app.api.v1.domains.entities.enums import CategoryName, EntityTypeName


class TestLocationsEndpoints:
    """Integration tests for Locations endpoints."""

    def _seed_dependencies(self, db: Session) -> dict:
        """Create required Category and EntityType records and return their IDs."""
        category = Category(name=CategoryName.MYTH, description="A myth category")
        entity_type = EntityType(
            name=EntityTypeName.CHARACTER, description="A character type"
        )
        db.add_all([category, entity_type])
        db.commit()
        return {"category_id": category.id, "entity_type_id": entity_type.id}

    def test_list_locations_empty(self, client: TestClient):
        """Test listing locations when database is empty."""
        response = client.get("/api/v1/locations/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_locations(self, client: TestClient, db: Session):
        """Test listing all locations."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        locations = [
            Location(
                entity_id=entity.id,
                department="Cundinamarca",
                municipality="Bogota",
                place_description="Capital city",
            ),
            Location(
                entity_id=entity.id,
                department="Oaxaca",
                municipality="Tlacolula",
                place_description="Valley town",
            ),
        ]
        db.add_all(locations)
        db.commit()

        response = client.get("/api/v1/locations/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_filter_locations_by_department(self, client: TestClient, db: Session):
        """Test filtering locations by department query parameter."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        locations = [
            Location(
                entity_id=entity.id,
                department="Cundinamarca",
                municipality="Bogota",
            ),
            Location(
                entity_id=entity.id,
                department="Antioquia",
                municipality="Medellin",
            ),
        ]
        db.add_all(locations)
        db.commit()

        response = client.get("/api/v1/locations/?department=Cundinamarca")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["department"] == "Cundinamarca"

    def test_filter_locations_by_department_partial_match(
        self, client: TestClient, db: Session
    ):
        """Test that department filter uses partial (LIKE) matching."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        locations = [
            Location(
                entity_id=entity.id,
                department="San Antonio",
                municipality="City",
            ),
            Location(
                entity_id=entity.id,
                department="San Francisco",
                municipality="City",
            ),
            Location(
                entity_id=entity.id,
                department="New York",
                municipality="City",
            ),
        ]
        db.add_all(locations)
        db.commit()

        response = client.get("/api/v1/locations/?department=San")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_get_location_by_id(self, client: TestClient, db: Session):
        """Test getting a single location by its numeric ID."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        location = Location(
            entity_id=entity.id,
            department="Cundinamarca",
            municipality="Bogota",
            place_description="Capital city",
        )
        db.add(location)
        db.commit()

        response = client.get(f"/api/v1/locations/{location.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == location.id
        assert data["department"] == "Cundinamarca"

    def test_get_location_by_id_not_found(self, client: TestClient):
        """Test getting a non-existent location by ID returns 404."""
        response = client.get("/api/v1/locations/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_location_by_id_does_not_collide_with_department_route(
        self, client: TestClient, db: Session
    ):
        """A numeric ID path segment must resolve via the /{id} route, not be
        swallowed by the string-typed /{department} route."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        department_only = Location(
            entity_id=entity.id,
            department="42",
            municipality="Numeric Department",
        )
        real_location = Location(
            entity_id=entity.id,
            department="Cundinamarca",
        )
        db.add_all([department_only, real_location])
        db.commit()

        # Request by the real location's numeric ID should return a single
        # object (LocationSchema), not a list from the department route.
        response = client.get(f"/api/v1/locations/{real_location.id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["id"] == real_location.id

    def test_get_locations_by_department_path(self, client: TestClient, db: Session):
        """Test getting locations by department via path parameter."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        locations = [
            Location(
                entity_id=entity.id,
                department="Oaxaca",
                municipality="Oaxaca City",
            ),
            Location(
                entity_id=entity.id,
                department="Oaxaca",
                municipality="Tlacolula",
            ),
            Location(
                entity_id=entity.id,
                department="Chiapas",
                municipality="San Cristobal",
            ),
        ]
        db.add_all(locations)
        db.commit()

        response = client.get("/api/v1/locations/Oaxaca")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(loc["department"] == "Oaxaca" for loc in data)

    def test_get_locations_by_department_empty_result(
        self, client: TestClient, db: Session
    ):
        """Test getting locations for a department with no locations."""
        response = client.get("/api/v1/locations/NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_location_response_schema(self, client: TestClient, db: Session):
        """Test that location response matches expected schema."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        location = Location(
            entity_id=entity.id,
            department="TestDept",
            municipality="TestMuni",
            place_description="Test description",
        )
        db.add(location)
        db.commit()

        response = client.get("/api/v1/locations/")
        assert response.status_code == 200
        data = response.json()
        loc = data["items"][0]
        assert "id" in loc
        assert "entity_id" in loc
        assert "department" in loc
        assert "municipality" in loc
        assert "place_description" in loc

    def test_create_location(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test creating a location as superuser."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.post(
            "/api/v1/locations/",
            json={
                "department": "Sonsonate",
                "municipality": "Izalco",
                "entity_id": entity.id,
            },
            headers=superuser_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["department"] == "Sonsonate"
        assert data["entity_id"] == entity.id

    def test_create_location_missing_entity_id_rejected(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test creating a location without entity_id returns 422, not a 500."""
        response = client.post(
            "/api/v1/locations/",
            json={"department": "Sonsonate"},
            headers=superuser_headers,
        )
        assert response.status_code == 422

    def test_create_location_without_auth(self, client: TestClient):
        """Test creating a location without auth returns 401."""
        response = client.post(
            "/api/v1/locations/",
            json={"department": "Sonsonate", "entity_id": 1},
        )
        assert response.status_code == 401

    def test_create_location_nonexistent_entity_id_returns_404(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test creating a location with an entity_id that doesn't exist
        returns 404 (a foreign-key violation), not 409 (which would
        incorrectly imply the location itself already exists)."""
        response = client.post(
            "/api/v1/locations/",
            json={"department": "Sonsonate", "entity_id": 999999},
            headers=superuser_headers,
        )
        assert response.status_code == 404

    def test_update_location(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test updating a location as superuser."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity 2",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        loc = Location(department="Old Dept", entity_id=entity.id)
        db.add(loc)
        db.commit()

        response = client.put(
            f"/api/v1/locations/{loc.id}",
            json={"department": "New Dept"},
            headers=superuser_headers,
        )
        assert response.status_code == 200
        assert response.json()["department"] == "New Dept"

    def test_delete_location(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test deleting a location as superuser."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity 3",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        loc = Location(department="To Delete", entity_id=entity.id)
        db.add(loc)
        db.commit()
        loc_id = loc.id

        response = client.delete(
            f"/api/v1/locations/{loc_id}", headers=superuser_headers
        )
        assert response.status_code == 204

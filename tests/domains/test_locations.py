"""
Tests for Locations domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.entities.models.location import Location


class TestLocationsEndpoints:
    """Integration tests for Locations endpoints."""

    def test_list_locations_empty(self, client: TestClient):
        """Test listing locations when database is empty."""
        response = client.get("/api/v1/locations/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_locations(self, client: TestClient, db: Session):
        """Test listing all locations."""
        locations = [
            Location(
                entity_id=1,
                department="Cundinamarca",
                municipality="Bogota",
                place_description="Capital city",
            ),
            Location(
                entity_id=1,
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
        locations = [
            Location(
                entity_id=1,
                department="Cundinamarca",
                municipality="Bogota",
            ),
            Location(
                entity_id=1,
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
        locations = [
            Location(
                entity_id=1,
                department="San Antonio",
                municipality="City",
            ),
            Location(
                entity_id=1,
                department="San Francisco",
                municipality="City",
            ),
            Location(
                entity_id=1,
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
        location = Location(
            entity_id=1,
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
        department_only = Location(
            entity_id=1,
            department="42",
            municipality="Numeric Department",
        )
        real_location = Location(
            entity_id=1,
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
        locations = [
            Location(
                entity_id=1,
                department="Oaxaca",
                municipality="Oaxaca City",
            ),
            Location(
                entity_id=1,
                department="Oaxaca",
                municipality="Tlacolula",
            ),
            Location(
                entity_id=1,
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
        location = Location(
            entity_id=1,
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

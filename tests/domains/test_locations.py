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
        assert data == []

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
        assert len(data) == 2

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
        assert len(data) == 1
        assert data[0]["department"] == "Cundinamarca"

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
        assert len(data) == 2

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
        loc = data[0]
        assert "id" in loc
        assert "entity_id" in loc
        assert "department" in loc
        assert "municipality" in loc
        assert "place_description" in loc

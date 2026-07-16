"""
Tests for Countries domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.countries.models.country import Country
from app.api.v1.domains.countries.schemas.country import CountryCreate
from app.api.v1.domains.countries.services.country import country as country_service


class TestCountryService:
    """Unit tests for CountryService."""

    def test_create_country(self, db: Session):
        """Test creating a country."""
        from app.api.v1.domains.countries.schemas.country import CountryCreate

        country_in = CountryCreate(name="El Salvador", status=True)
        created = country_service.create(db, obj_in=country_in)

        assert created.name == "El Salvador"
        assert created.status is True
        assert created.id is not None

    def test_get_country(self, db: Session):
        """Test getting a country by ID."""
        country = Country(name="Guatemala", status=True)
        db.add(country)
        db.commit()

        retrieved = country_service.get(db, item_id=country.id)

        assert retrieved is not None
        assert retrieved.name == "Guatemala"

    def test_get_country_not_found(self, db: Session):
        """Test getting a non-existent country."""
        retrieved = country_service.get(db, item_id=999)
        assert retrieved is None

    def test_update_country(self, db: Session):
        """Test updating a country."""
        from app.api.v1.domains.countries.schemas.country import CountryUpdate

        # Use the service to create the country for consistency
        country_in = CountryCreate(name="Honduras", status=True)
        country = country_service.create(db, obj_in=country_in)

        update_in = CountryUpdate(name="Republic of Honduras")
        updated = country_service.update(db, db_obj=country, obj_in=update_in)

        assert updated.name == "Republic of Honduras"

    def test_delete_country(self, db: Session):
        """Test deleting a country."""
        country = Country(name="Nicaragua", status=True)
        db.add(country)
        db.commit()
        country_id = country.id

        country_service.remove(db, item_id=country_id)

        deleted = country_service.get(db, item_id=country_id)
        assert deleted is None

    def test_get_multi_countries(self, db: Session):
        """Test getting multiple countries."""
        countries = [
            Country(name="Costa Rica", status=True),
            Country(name="Panama", status=True),
            Country(name="Belize", status=False),
        ]
        db.add_all(countries)
        db.commit()

        all_countries = country_service.get_multi(db)

        assert len(all_countries) == 3


class TestCountriesEndpoints:
    """Integration tests for Countries endpoints."""

    def test_list_countries_empty(self, client: TestClient):
        """Test listing countries when database is empty."""
        response = client.get("/api/v1/countries/")
        assert response.status_code == 200
        data = response.json()
        # Direct response (no ApiResponse wrapper)
        assert data == []

    def test_list_countries(self, client: TestClient, db: Session):
        """Test listing countries with data."""
        countries = [
            Country(name="El Salvador", status=True),
            Country(name="Guatemala", status=True),
        ]
        db.add_all(countries)
        db.commit()

        response = client.get("/api/v1/countries/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_create_country(self, client: TestClient, superuser_headers: dict):
        """Test creating a country."""
        response = client.post(
            "/api/v1/countries/",
            headers=superuser_headers,
            json={"name": "El Salvador", "status": True},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "El Salvador"
        assert data["status"] is True

    def test_get_country_by_id(self, client: TestClient, db: Session):
        """Test getting a country by ID."""
        country = Country(name="Honduras", status=True)
        db.add(country)
        db.commit()

        response = client.get(f"/api/v1/countries/{country.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Honduras"

    def test_get_country_not_found(self, client: TestClient):
        """Test getting a non-existent country."""
        response = client.get("/api/v1/countries/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_update_country(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test updating a country."""
        country = Country(name="Nicaragua", status=True)
        db.add(country)
        db.commit()

        response = client.put(
            f"/api/v1/countries/{country.id}",
            headers=superuser_headers,
            json={"name": "Republic of Nicaragua"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Republic of Nicaragua"

    def test_delete_country(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test deleting a country."""
        country = Country(name="Costa Rica", status=True)
        db.add(country)
        db.commit()

        response = client.delete(f"/api/v1/countries/{country.id}", headers=superuser_headers)
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/api/v1/countries/{country.id}")
        assert response.status_code == 404

    def test_create_country_without_auth(self, client: TestClient):
        """Test creating a country without authentication returns 401."""
        response = client.post(
            "/api/v1/countries/",
            json={"name": "Belize", "status": True},
        )
        assert response.status_code == 401

    def test_create_country_as_regular_user(self, client: TestClient, auth_headers: dict):
        """Test creating a country as non-superuser returns 403."""
        response = client.post(
            "/api/v1/countries/",
            headers=auth_headers,
            json={"name": "Belize", "status": True},
        )
        assert response.status_code == 403

    def test_update_country_without_auth(self, client: TestClient, db: Session):
        """Test updating a country without authentication returns 401."""
        country = Country(name="Panama", status=True)
        db.add(country)
        db.commit()

        response = client.put(
            f"/api/v1/countries/{country.id}",
            json={"name": "Hacked"},
        )
        assert response.status_code == 401

    def test_update_country_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test updating a country as non-superuser returns 403."""
        country = Country(name="Panama", status=True)
        db.add(country)
        db.commit()

        response = client.put(
            f"/api/v1/countries/{country.id}",
            headers=auth_headers,
            json={"name": "Hacked"},
        )
        assert response.status_code == 403

    def test_delete_country_without_auth(self, client: TestClient, db: Session):
        """Test deleting a country without authentication returns 401."""
        country = Country(name="Belize", status=True)
        db.add(country)
        db.commit()

        response = client.delete(f"/api/v1/countries/{country.id}")
        assert response.status_code == 401

    def test_delete_country_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test deleting a country as non-superuser returns 403."""
        country = Country(name="Belize", status=True)
        db.add(country)
        db.commit()

        response = client.delete(f"/api/v1/countries/{country.id}", headers=auth_headers)
        assert response.status_code == 403

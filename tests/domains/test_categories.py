"""
Tests for Categories domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.entities.models.category import Category
from app.api.v1.domains.entities.enums import CategoryName


class TestCategoriesEndpoints:
    """Integration tests for Categories endpoints."""

    def test_list_categories_empty(self, client: TestClient):
        """Test listing categories when database is empty."""
        response = client.get("/api/v1/categories/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_categories(self, client: TestClient, db: Session):
        """Test listing all categories."""
        categories = [
            Category(name=CategoryName.MYTH, description="Myths and mythological tales"),
            Category(name=CategoryName.LEGEND, description="Legends from folklore"),
            Category(name=CategoryName.TRADITION, description="Cultural traditions"),
        ]
        db.add_all(categories)
        db.commit()

        response = client.get("/api/v1/categories/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_categories_sorted_by_name_asc(self, client: TestClient, db: Session):
        """Test that categories are sorted by name ascending by default."""
        categories = [
            Category(name=CategoryName.TRADITION, description="Traditions"),
            Category(name=CategoryName.MYTH, description="Myths"),
            Category(name=CategoryName.LEGEND, description="Legends"),
        ]
        db.add_all(categories)
        db.commit()

        response = client.get("/api/v1/categories/")
        assert response.status_code == 200
        data = response.json()
        names = [c["name"] for c in data["items"]]
        assert names == sorted(names)

    def test_list_categories_sorted_desc(self, client: TestClient, db: Session):
        """Test listing categories sorted descending."""
        categories = [
            Category(name=CategoryName.MYTH, description="Myths"),
            Category(name=CategoryName.LEGEND, description="Legends"),
        ]
        db.add_all(categories)
        db.commit()

        response = client.get("/api/v1/categories/?order=desc")
        assert response.status_code == 200
        data = response.json()
        names = [c["name"] for c in data["items"]]
        assert names == sorted(names, reverse=True)

    def test_list_categories_invalid_sort_field_rejected(self, client: TestClient):
        """Test that an invalid sort field is rejected with a 422, rather than
        silently falling back to id like the old, unvalidated implementation."""
        response = client.get("/api/v1/categories/?sort=not_a_real_field")
        assert response.status_code == 422

    def test_list_categories_invalid_order_value_rejected(self, client: TestClient):
        """Test that an invalid order value is rejected with a 422, rather
        than silently falling back to ascending."""
        response = client.get("/api/v1/categories/?order=sideways")
        assert response.status_code == 422

    def test_get_category_by_id(self, client: TestClient, db: Session):
        """Test getting a category by ID."""
        category = Category(
            name=CategoryName.MYTH, description="Myths and mythological tales"
        )
        db.add(category)
        db.commit()

        response = client.get(f"/api/v1/categories/{category.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MYTH"
        assert data["description"] == "Myths and mythological tales"
        assert "id" in data
        assert "entity_count" in data

    def test_get_category_not_found(self, client: TestClient):
        """Test getting a non-existent category."""
        response = client.get("/api/v1/categories/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_category_response_schema(self, client: TestClient, db: Session):
        """Test that category response matches expected schema."""
        category = Category(name=CategoryName.LEGEND, description="Folklore legends")
        db.add(category)
        db.commit()

        response = client.get(f"/api/v1/categories/{category.id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "entity_count" in data

    def test_create_category(self, client: TestClient, superuser_headers: dict):
        """Test creating a category as superuser."""
        response = client.post(
            "/api/v1/categories/",
            json={"name": "TRADITION", "description": "Objects with special significance"},
            headers=superuser_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "TRADITION"
        assert data["description"] == "Objects with special significance"
        assert "id" in data

    def test_create_category_without_auth(self, client: TestClient):
        """Test creating a category without auth returns 401."""
        response = client.post(
            "/api/v1/categories/",
            json={"name": "TRADITION", "description": "test"},
        )
        assert response.status_code == 401

    def test_create_category_as_regular_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a category as non-superuser returns 403."""
        response = client.post(
            "/api/v1/categories/",
            json={"name": "TRADITION", "description": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_category(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test updating a category as superuser."""
        category = Category(name=CategoryName.MYTH, description="Original description")
        db.add(category)
        db.commit()

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json={"description": "Updated description"},
            headers=superuser_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["name"] == "MYTH"

    def test_update_category_without_auth(self, client: TestClient, db: Session):
        """Test updating a category without authentication returns 401."""
        category = Category(name=CategoryName.MYTH, description="Original description")
        db.add(category)
        db.commit()

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json={"description": "Updated description"},
        )
        assert response.status_code == 401

    def test_update_category_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test updating a category as non-superuser returns 403."""
        category = Category(name=CategoryName.MYTH, description="Original description")
        db.add(category)
        db.commit()

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_category_not_found(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test updating a non-existent category returns 404."""
        response = client.put(
            "/api/v1/categories/99999",
            json={"description": "test"},
            headers=superuser_headers,
        )
        assert response.status_code == 404

    def test_delete_category(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test deleting a category as superuser."""
        category = Category(name=CategoryName.TRADITION, description="test")
        db.add(category)
        db.commit()
        category_id = category.id

        response = client.delete(
            f"/api/v1/categories/{category_id}", headers=superuser_headers
        )
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/categories/{category_id}")
        assert get_response.status_code == 404

    def test_delete_category_without_auth(self, client: TestClient, db: Session):
        """Test deleting a category without authentication returns 401."""
        category = Category(name=CategoryName.TRADITION, description="test")
        db.add(category)
        db.commit()

        response = client.delete(f"/api/v1/categories/{category.id}")
        assert response.status_code == 401

    def test_delete_category_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test deleting a category as non-superuser returns 403."""
        category = Category(name=CategoryName.TRADITION, description="test")
        db.add(category)
        db.commit()

        response = client.delete(
            f"/api/v1/categories/{category.id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_delete_category_not_found(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test deleting a non-existent category returns 404."""
        response = client.delete(
            "/api/v1/categories/99999", headers=superuser_headers
        )
        assert response.status_code == 404

    def test_create_category_duplicate_name_returns_409(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test creating a category with a name that already exists returns
        409, not an unhandled IntegrityError (Category.name is unique)."""
        db.add(Category(name=CategoryName.MYTH, description="Existing"))
        db.commit()

        response = client.post(
            "/api/v1/categories/",
            json={"name": "MYTH", "description": "Duplicate"},
            headers=superuser_headers,
        )
        assert response.status_code == 409

    def test_create_category_invalid_name_rejected(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test creating a category with a name outside the CategoryName enum
        is rejected with 422 by Pydantic validation, not silently accepted."""
        response = client.post(
            "/api/v1/categories/",
            json={"name": "NOT_A_REAL_CATEGORY", "description": "test"},
            headers=superuser_headers,
        )
        assert response.status_code == 422

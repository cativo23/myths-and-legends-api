"""
Tests for Categories domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.entities.models.category import Category
from app.api.v1.entities.enums import CategoryName


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

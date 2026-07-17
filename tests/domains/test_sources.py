"""
Tests for Sources domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.entities.models.source import Source
from app.api.v1.domains.entities.enums import SourceType
from app.api.v1.domains.entities.models.category import Category
from app.api.v1.domains.entities.models.entity import Entity
from app.api.v1.domains.entities.models.entity_type import EntityType
from app.api.v1.domains.entities.enums import CategoryName, EntityTypeName


class TestSourcesEndpoints:
    """Integration tests for Sources endpoints."""

    def _seed_dependencies(self, db: Session) -> dict:
        """Create required Category and EntityType records and return their IDs."""
        category = Category(name=CategoryName.MYTH, description="A myth category")
        entity_type = EntityType(
            name=EntityTypeName.CHARACTER, description="A character type"
        )
        db.add_all([category, entity_type])
        db.commit()
        return {"category_id": category.id, "entity_type_id": entity_type.id}

    def test_list_sources_empty(self, client: TestClient):
        """Test listing sources when database is empty."""
        response = client.get("/api/v1/sources/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_sources(self, client: TestClient, db: Session):
        """Test listing all sources."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        sources = [
            Source(
                entity_id=entity.id,
                source_type=SourceType.BOOK,
                title="The Golden Bough",
                author="James Frazer",
                url="https://example.com/golden-bough",
            ),
            Source(
                entity_id=entity.id,
                source_type=SourceType.WEB,
                title="Mythology Archive",
                author=None,
                url="https://example.com/archive",
            ),
        ]
        db.add_all(sources)
        db.commit()

        response = client.get("/api/v1/sources/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_sources_sorted_by_title(self, client: TestClient, db: Session):
        """Test sorting sources by title field."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        sources = [
            Source(entity_id=entity.id, source_type=SourceType.BOOK, title="Zebra Book"),
            Source(entity_id=entity.id, source_type=SourceType.BOOK, title="Alpha Book"),
        ]
        db.add_all(sources)
        db.commit()

        # Source model has no 'name' field, so default sort is 'id'.
        # Explicitly sort by 'title' to test title-based ordering
        response = client.get("/api/v1/sources/?sort=title")
        assert response.status_code == 200
        data = response.json()
        titles = [s["title"] for s in data["items"]]
        assert titles == sorted(titles)

    def test_list_sources_invalid_sort_field_rejected(self, client: TestClient):
        """Test that an invalid sort field is rejected with a 422, rather than
        silently falling back to id like the old, unvalidated implementation."""
        response = client.get("/api/v1/sources/?sort=not_a_real_field")
        assert response.status_code == 422

    def test_list_sources_sorted_desc(self, client: TestClient, db: Session):
        """Test listing sources sorted descending."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        sources = [
            Source(entity_id=entity.id, source_type=SourceType.BOOK, title="Alpha Book"),
            Source(entity_id=entity.id, source_type=SourceType.BOOK, title="Beta Book"),
        ]
        db.add_all(sources)
        db.commit()

        response = client.get("/api/v1/sources/?order=desc")
        assert response.status_code == 200
        data = response.json()
        titles = [s["title"] for s in data["items"]]
        assert titles == sorted(titles, reverse=True)

    def test_filter_sources_by_type(self, client: TestClient, db: Session):
        """Test filtering sources by source type."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        sources = [
            Source(
                entity_id=entity.id,
                source_type=SourceType.BOOK,
                title="A Book",
            ),
            Source(
                entity_id=entity.id,
                source_type=SourceType.WEB,
                title="A Website",
            ),
            Source(
                entity_id=entity.id,
                source_type=SourceType.ORAL_TRADITION,
                title="Oral Story",
            ),
        ]
        db.add_all(sources)
        db.commit()

        response = client.get("/api/v1/sources/?source_type=BOOK")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["source_type"] == "BOOK"

    def test_source_response_schema(self, client: TestClient, db: Session):
        """Test that source response matches expected schema."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        source = Source(
            entity_id=entity.id,
            source_type=SourceType.DOCUMENT,
            title="Historical Document",
            author="Anonymous",
            url="https://example.com/doc",
        )
        db.add(source)
        db.commit()

        response = client.get("/api/v1/sources/")
        assert response.status_code == 200
        data = response.json()
        s = data["items"][0]
        assert "id" in s
        assert "entity_id" in s
        assert "source_type" in s
        assert "title" in s
        assert "author" in s
        assert "url" in s

    def test_get_source_by_id(self, client: TestClient, db: Session):
        """Test getting a single source by its ID."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        source = Source(
            entity_id=entity.id,
            source_type=SourceType.BOOK,
            title="The Golden Bough",
        )
        db.add(source)
        db.commit()

        response = client.get(f"/api/v1/sources/{source.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == source.id
        assert data["title"] == "The Golden Bough"

    def test_get_source_by_id_not_found(self, client: TestClient):
        """Test getting a non-existent source by ID returns 404."""
        response = client.get("/api/v1/sources/999")
        assert response.status_code == 404

    def test_create_source(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test creating a source as superuser."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.post(
            "/api/v1/sources/",
            json={
                "source_type": "BOOK",
                "title": "Test Source Title",
                "author": "Test Author",
                "entity_id": entity.id,
            },
            headers=superuser_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Source Title"
        assert data["entity_id"] == entity.id

    def test_create_source_missing_entity_id_rejected(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test creating a source without entity_id returns 422, not a 500."""
        response = client.post(
            "/api/v1/sources/",
            json={"source_type": "BOOK", "title": "Test Source"},
            headers=superuser_headers,
        )
        assert response.status_code == 422

    def test_create_source_without_auth(self, client: TestClient):
        """Test creating a source without auth returns 401."""
        response = client.post(
            "/api/v1/sources/",
            json={"source_type": "BOOK", "title": "Test Source", "entity_id": 1},
        )
        assert response.status_code == 401

    def test_create_source_nonexistent_entity_id_returns_404(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test creating a source with an entity_id that doesn't exist
        returns 404 (a foreign-key violation), not 409 (which would
        incorrectly imply the source itself already exists)."""
        response = client.post(
            "/api/v1/sources/",
            json={
                "source_type": "BOOK",
                "title": "Test Source",
                "entity_id": 999999,
            },
            headers=superuser_headers,
        )
        assert response.status_code == 404

    def test_update_source(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test updating a source as superuser."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity 2",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        source = Source(
            source_type=SourceType.BOOK, title="Old Title", entity_id=entity.id
        )
        db.add(source)
        db.commit()

        response = client.put(
            f"/api/v1/sources/{source.id}",
            json={"title": "New Title"},
            headers=superuser_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"

    def test_delete_source(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test deleting a source as superuser."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Test Entity 3",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        source = Source(
            source_type=SourceType.WEB, title="To Delete", entity_id=entity.id
        )
        db.add(source)
        db.commit()
        source_id = source.id

        response = client.delete(
            f"/api/v1/sources/{source_id}", headers=superuser_headers
        )
        assert response.status_code == 204

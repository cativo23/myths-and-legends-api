"""
Tests for Sources domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.entities.models.source import Source
from app.api.v1.entities.enums import SourceType


class TestSourcesEndpoints:
    """Integration tests for Sources endpoints."""

    def test_list_sources_empty(self, client: TestClient):
        """Test listing sources when database is empty."""
        response = client.get("/api/v1/sources/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_sources(self, client: TestClient, db: Session):
        """Test listing all sources."""
        sources = [
            Source(
                entity_id=1,
                source_type=SourceType.BOOK,
                title="The Golden Bough",
                author="James Frazer",
                url="https://example.com/golden-bough",
            ),
            Source(
                entity_id=1,
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
        sources = [
            Source(entity_id=1, source_type=SourceType.BOOK, title="Zebra Book"),
            Source(entity_id=1, source_type=SourceType.BOOK, title="Alpha Book"),
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
        sources = [
            Source(entity_id=1, source_type=SourceType.BOOK, title="Alpha Book"),
            Source(entity_id=1, source_type=SourceType.BOOK, title="Beta Book"),
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
        sources = [
            Source(
                entity_id=1,
                source_type=SourceType.BOOK,
                title="A Book",
            ),
            Source(
                entity_id=1,
                source_type=SourceType.WEB,
                title="A Website",
            ),
            Source(
                entity_id=1,
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
        source = Source(
            entity_id=1,
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

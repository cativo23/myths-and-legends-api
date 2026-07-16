"""
Tests for Home domain.
"""
import pytest
from fastapi.testclient import TestClient


class TestHomeEndpoints:
    """Integration tests for Home endpoints."""

    def test_home(self, client: TestClient):
        """Test home/welcome endpoint."""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Welcome to" in data["message"]
        assert "v1" in data["message"]
        assert "data" in data
        assert data["data"]["current_version"] == "v1.0.0"
        assert "urls" in data["data"]

    def test_home_urls_contain_docs_links(self, client: TestClient):
        """Test that home endpoint returns documentation URLs."""
        response = client.get("/api/v1/")
        data = response.json()
        urls = data["data"]["urls"]
        url_keys = [list(u.keys())[0] for u in urls]
        assert "openapi" in url_keys
        assert "docs" in url_keys
        assert "redoc" in url_keys

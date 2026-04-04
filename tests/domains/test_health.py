"""
Tests for Health domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestHealthEndpoints:
    """Integration tests for Health endpoints."""

    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "myths-and-legends-api"
        assert "timestamp" in data

    def test_health_check_trailing_slash(self, client: TestClient):
        """Test basic health check endpoint with trailing slash."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "myths-and-legends-api"
        assert "timestamp" in data

    def test_liveness_probe(self, client: TestClient):
        """Test liveness probe endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["service"] == "myths-and-legends-api"
        assert "timestamp" in data

    def test_readiness_probe_healthy(self, client: TestClient, db: Session):
        """Test readiness probe when database is healthy."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "myths-and-legends-api"
        assert "timestamp" in data
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"

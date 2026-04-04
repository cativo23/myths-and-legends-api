"""
Tests for Images domain.
"""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestImagesEndpoints:
    """Integration tests for Images endpoints."""

    def test_get_valid_image(self, client: TestClient):
        """Test retrieving a valid image file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a fake image file
            test_file = os.path.join(tmp_dir, "test_image.png")
            with open(test_file, "wb") as f:
                f.write(b"\x89PNG fake image content")

            with patch("app.api.v1.domains.images.endpoints.images.getcwd", return_value=tmp_dir):
                # Create the expected directory structure
                images_dir = os.path.join(tmp_dir, "app", "images")
                os.makedirs(images_dir, exist_ok=True)
                # Move the test file to the images dir
                os.rename(test_file, os.path.join(images_dir, "test_image.png"))

                response = client.get("/api/v1/images/test_image.png")
                assert response.status_code == 200

    def test_get_invalid_extension(self, client: TestClient):
        """Test that disallowed extensions return 400."""
        response = client.get("/api/v1/images/document.pdf")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid file extension" in data["detail"]

    def test_get_path_traversal_dotdot(self, client: TestClient):
        """Test that path traversal with '..' is blocked."""
        # FastAPI normalizes ../ out of the path, so we test URL-encoded version
        response = client.get("/api/v1/images/%2e%2e%2f%2e%2e%2fetc%2fpasswd")
        # Either 400 (blocked by endpoint) or 404 (normalized path not found) is acceptable
        assert response.status_code in (400, 404)

    def test_get_path_traversal_slash(self, client: TestClient):
        """Test that path traversal with '/' in filename is blocked."""
        # FastAPI normalizes paths, so embedded slashes become separate path segments
        # This should hit the endpoint's slash check for the first segment
        response = client.get("/api/v1/images/subdir%2Fimage.png")
        assert response.status_code in (400, 404)

    def test_get_nonexistent_file(self, client: TestClient):
        """Test that a non-existent image returns 404."""
        response = client.get("/api/v1/images/nonexistent.png")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Image not found" in data["detail"]

"""
Pytest configuration and fixtures for testing.

Provides database sessions, test client, and authentication helpers.
"""
import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.sqlite import base as sqlite_base

from app.main import app
from app.db.base_class import Base
from app.core.config import settings
from app.api.v1.domains.users.services.user import user as user_service
from app.api.v1.domains.users.schemas.user import UserCreate
from app.core.security import verify_password


# Monkey-patch SQLite to support ARRAY type as JSON
# This is needed because the Entity model uses ARRAY(String) for alternative_names
# which SQLite doesn't support natively
def visit_ARRAY(self, type_, **kw):
    return "JSON"


sqlite_base.SQLiteTypeCompiler.visit_ARRAY = visit_ARRAY

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.

    Each test gets a completely fresh SQLite database file.
    """
    # Create a temporary database file for this test
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        test_engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )

        # Create all tables
        Base.metadata.create_all(bind=test_engine)

        # Create session
        connection = test_engine.connect()
        transaction = connection.begin()
        session = TestingSessionLocal(bind=connection)

        yield session

        # Cleanup
        session.close()
        transaction.rollback()
        connection.close()
    finally:
        # Remove temporary database file
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.
    """
    from app.api.v1.shared.deps import get_db

    def get_db_override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = get_db_override

    with TestClient(app=app) as test_client:
        yield test_client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def test_user(db: Session) -> dict:
    """Create a test user and return credentials."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_superuser": False,
        "is_active": True,
    }

    user_in = UserCreate(**user_data)
    user = user_service.create(db, obj_in=user_in)

    return {
        "id": user.id,
        "email": user_data["email"],
        "password": user_data["password"],
        "user": user,
    }


@pytest.fixture(scope="function")
def superuser(db: Session) -> dict:
    """Create a superuser and return credentials."""
    user_data = {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "is_superuser": True,
        "is_active": True,
    }

    user_in = UserCreate(**user_data)
    user = user_service.create(db, obj_in=user_in)

    return {
        "id": user.id,
        "email": user_data["email"],
        "password": user_data["password"],
        "user": user,
    }


@pytest.fixture
def auth_headers(client: TestClient, test_user: dict) -> dict:
    """Get authentication headers for a test user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user["email"], "password": test_user["password"]},
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def superuser_headers(client: TestClient, superuser: dict) -> dict:
    """Get authentication headers for a superuser."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": superuser["email"], "password": superuser["password"]},
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}

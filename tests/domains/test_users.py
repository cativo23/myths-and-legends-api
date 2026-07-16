"""
Tests for Users domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.users.models.user import User
from app.api.v1.domains.users.schemas.user import UserCreate
from app.api.v1.domains.users.services.user import user as user_service


class TestUserService:
    """Unit tests for UserService."""

    def test_create_user(self, db: Session):
        """Test creating a user."""
        user_in = UserCreate(
            email="newuser@example.com",
            password="securepassword123",
            full_name="New User",
            is_superuser=False,
        )
        created = user_service.create(db, obj_in=user_in)

        assert created.email == "newuser@example.com"
        assert created.full_name == "New User"
        assert created.is_superuser is False
        assert created.is_active is True
        assert created.id is not None

    def test_get_user(self, db: Session):
        """Test getting a user by ID."""
        user = User(
            email="findme@example.com",
            hashed_password="hashed",
            full_name="Find Me",
        )
        db.add(user)
        db.commit()

        retrieved = user_service.get(db, item_id=user.id)

        assert retrieved is not None
        assert retrieved.email == "findme@example.com"

    def test_get_user_not_found(self, db: Session):
        """Test getting a non-existent user."""
        retrieved = user_service.get(db, item_id=999)
        assert retrieved is None

    def test_update_user(self, db: Session):
        """Test updating a user."""
        from app.api.v1.domains.users.schemas.user import UserUpdate

        user_in = UserCreate(
            email="updateme@example.com",
            password="securepassword123",
            full_name="Before Update",
        )
        user = user_service.create(db, obj_in=user_in)

        update_in = UserUpdate(full_name="After Update")
        updated = user_service.update(db, db_obj=user, obj_in=update_in)

        assert updated.full_name == "After Update"
        assert updated.email == "updateme@example.com"

    def test_update_user_password(self, db: Session):
        """Test updating a user's password hashes it."""
        from app.core.security import verify_password
        from app.api.v1.domains.users.schemas.user import UserUpdate

        user_in = UserCreate(
            email="newpass@example.com",
            password="oldpassword123",
        )
        user = user_service.create(db, obj_in=user_in)

        update_in = UserUpdate(password="newpassword123")
        updated = user_service.update(db, db_obj=user, obj_in=update_in)

        assert verify_password("newpassword123", updated.hashed_password)
        assert not verify_password("oldpassword123", updated.hashed_password)

    def test_delete_user(self, db: Session):
        """Test deleting a user."""
        user = User(
            email="deleteme@example.com",
            hashed_password="hashed",
        )
        db.add(user)
        db.commit()
        user_id = user.id

        user_service.remove(db, item_id=user_id)

        deleted = user_service.get(db, item_id=user_id)
        assert deleted is None

    def test_get_by_email(self, db: Session):
        """Test getting a user by email."""
        user_in = UserCreate(
            email="search@example.com",
            password="securepassword123",
        )
        user_service.create(db, obj_in=user_in)

        found = user_service.get_by_email(db, email="search@example.com")

        assert found is not None
        assert found.email == "search@example.com"

    def test_get_by_email_not_found(self, db: Session):
        """Test getting a non-existent user by email."""
        found = user_service.get_by_email(db, email="nope@example.com")
        assert found is None

    def test_get_multi_users(self, db: Session):
        """Test getting multiple users."""
        users = [
            User(
                email=f"user{i}@example.com",
                hashed_password="hashed",
                full_name=f"User {i}",
            )
            for i in range(3)
        ]
        db.add_all(users)
        db.commit()

        all_users = user_service.get_multi(db)

        assert len(all_users) == 3

    def test_is_active(self, db: Session):
        """Test is_active check."""
        active_user = User(
            email="active@example.com",
            hashed_password="hashed",
            is_active=True,
        )
        inactive_user = User(
            email="inactive@example.com",
            hashed_password="hashed",
            is_active=False,
        )

        assert user_service.is_active(active_user) is True
        assert user_service.is_active(inactive_user) is False

    def test_is_superuser(self, db: Session):
        """Test is_superuser check."""
        super_user = User(
            email="super@example.com",
            hashed_password="hashed",
            is_superuser=True,
        )
        regular_user = User(
            email="regular@example.com",
            hashed_password="hashed",
            is_superuser=False,
        )

        assert user_service.is_superuser(super_user) is True
        assert user_service.is_superuser(regular_user) is False

    def test_authenticate_success(self, db: Session):
        """Test successful authentication."""
        user_in = UserCreate(
            email="auth@example.com",
            password="mypassword123",
        )
        user_service.create(db, obj_in=user_in)

        authenticated = user_service.authenticate(
            db, email="auth@example.com", password="mypassword123"
        )

        assert authenticated is not None
        assert authenticated.email == "auth@example.com"

    def test_authenticate_wrong_password(self, db: Session):
        """Test authentication with wrong password."""
        user_in = UserCreate(
            email="wrongpass@example.com",
            password="correctpassword123",
        )
        user_service.create(db, obj_in=user_in)

        authenticated = user_service.authenticate(
            db, email="wrongpass@example.com", password="wrongpassword123"
        )

        assert authenticated is None

    def test_authenticate_wrong_email(self, db: Session):
        """Test authentication with non-existent email."""
        authenticated = user_service.authenticate(
            db, email="nobody@example.com", password="password123"
        )

        assert authenticated is None


class TestUsersEndpoints:
    """Integration tests for Users endpoints."""

    def test_get_all_users_empty(self, client: TestClient, superuser_headers: dict):
        """Test listing users when only the superuser (from the auth fixture) exists."""
        response = client.get("/api/v1/users/", headers=superuser_headers)
        assert response.status_code == 200
        data = response.json()
        # `superuser_headers` creates the admin user as a side effect of
        # authenticating, so "empty" means "just the superuser," not zero.
        assert len(data["items"]) == 1
        assert data["total"] == 1

    def test_get_all_users(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test listing users with data."""
        users = [
            User(
                email="alice@example.com",
                hashed_password="hashed",
                full_name="Alice",
            ),
            User(
                email="bob@example.com",
                hashed_password="hashed",
                full_name="Bob",
            ),
        ]
        db.add_all(users)
        db.commit()

        response = client.get("/api/v1/users/", headers=superuser_headers)
        assert response.status_code == 200
        data = response.json()
        # +1 for the superuser created by the `superuser_headers` fixture.
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_get_all_users_second_page_returns_remaining_rows(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Regression test for the double-pagination bug: page 2 of a
        multi-page user list used to come back empty with `total` equal to
        the page size, because `get_multi(skip, limit)` had already sliced
        the DB rows down to one page before `paginate()` re-sliced them a
        second time using the same page number."""
        # 24 extra users + 1 superuser (created by the `superuser_headers`
        # fixture) = 25 total rows, spanning 2 pages at size=20.
        users = [
            User(
                email=f"user{i}@example.com",
                hashed_password="hashed",
                full_name=f"User {i}",
            )
            for i in range(24)
        ]
        db.add_all(users)
        db.commit()

        response = client.get(
            "/api/v1/users/?page=2&size=20", headers=superuser_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["items"]) > 0
        assert len(data["items"]) == 5
        assert data["page"] == 2

    def test_create_user(self, client: TestClient, superuser_headers: dict):
        """Test creating a user as superuser."""
        response = client.post(
            "/api/v1/users/",
            headers=superuser_headers,
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
                "is_superuser": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_superuser"] is False
        assert data["is_active"] is True
        assert "id" in data
        assert "password" not in data

    def test_create_user_duplicate_email(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test creating a user with an existing email returns 400."""
        user = User(
            email="duplicate@example.com",
            hashed_password="hashed",
            full_name="Original",
        )
        db.add(user)
        db.commit()

        response = client.post(
            "/api/v1/users/",
            headers=superuser_headers,
            json={
                "email": "duplicate@example.com",
                "password": "anotherpassword123",
                "full_name": "Duplicate",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_create_user_without_auth(self, client: TestClient):
        """Test creating a user without authentication returns 401."""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "unauthorized@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 401

    def test_create_user_as_regular_user(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a user as non-superuser returns 403."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 403

    def test_get_user_by_id(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test getting a user by ID."""
        user = User(
            email="findme@example.com",
            hashed_password="hashed",
            full_name="Find Me",
        )
        db.add(user)
        db.commit()

        response = client.get(
            f"/api/v1/users/{user.id}", headers=superuser_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "findme@example.com"
        assert data["full_name"] == "Find Me"

    def test_get_user_not_found(self, client: TestClient, superuser_headers: dict):
        """Test getting a non-existent user returns 404."""
        response = client.get("/api/v1/users/999", headers=superuser_headers)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"

    def test_get_user_without_auth(self, client: TestClient):
        """Test getting a user without authentication returns 401."""
        response = client.get("/api/v1/users/1")
        assert response.status_code == 401

    def test_get_user_as_regular_user(self, client: TestClient, auth_headers: dict):
        """Test getting a user as non-superuser returns 403."""
        response = client.get("/api/v1/users/1", headers=auth_headers)
        assert response.status_code == 403

    def test_update_user(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test updating a user."""
        user = User(
            email="update@example.com",
            hashed_password="hashed",
            full_name="Old Name",
        )
        db.add(user)
        db.commit()

        response = client.put(
            f"/api/v1/users/{user.id}",
            headers=superuser_headers,
            json={"full_name": "New Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "New Name"
        assert data["email"] == "update@example.com"

    def test_update_user_not_found(self, client: TestClient, superuser_headers: dict):
        """Test updating a non-existent user returns 404."""
        response = client.put(
            "/api/v1/users/999",
            headers=superuser_headers,
            json={"full_name": "Nobody"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"

    def test_update_user_without_auth(self, client: TestClient):
        """Test updating a user without authentication returns 401."""
        response = client.put(
            "/api/v1/users/1",
            json={"full_name": "Hacker"},
        )
        assert response.status_code == 401

    def test_update_user_as_regular_user(self, client: TestClient, auth_headers: dict):
        """Test updating a user as non-superuser returns 403."""
        response = client.put(
            "/api/v1/users/1",
            headers=auth_headers,
            json={"full_name": "Hacker"},
        )
        assert response.status_code == 403

    def test_delete_user(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test deleting a user."""
        user = User(
            email="delete@example.com",
            hashed_password="hashed",
        )
        db.add(user)
        db.commit()

        response = client.delete(
            f"/api/v1/users/{user.id}", headers=superuser_headers
        )
        assert response.status_code == 204

        # Verify deletion
        response = client.get(
            f"/api/v1/users/{user.id}", headers=superuser_headers
        )
        assert response.status_code == 404

    def test_delete_user_not_found(self, client: TestClient, superuser_headers: dict):
        """Test deleting a non-existent user returns 404."""
        response = client.delete("/api/v1/users/999", headers=superuser_headers)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"

    def test_delete_user_without_auth(self, client: TestClient):
        """Test deleting a user without authentication returns 401."""
        response = client.delete("/api/v1/users/1")
        assert response.status_code == 401

    def test_delete_user_as_regular_user(self, client: TestClient, auth_headers: dict):
        """Test deleting a user as non-superuser returns 403."""
        response = client.delete("/api/v1/users/1", headers=auth_headers)
        assert response.status_code == 403

    def test_list_users_without_auth(self, client: TestClient):
        """Test listing users without authentication returns 401."""
        response = client.get("/api/v1/users/")
        assert response.status_code == 401

    def test_list_users_as_regular_user(self, client: TestClient, auth_headers: dict):
        """Test listing users as non-superuser returns 403."""
        response = client.get("/api/v1/users/", headers=auth_headers)
        assert response.status_code == 403

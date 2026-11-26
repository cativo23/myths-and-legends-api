"""
Tests for Entities domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.entities.models.entity import Entity
from app.api.v1.domains.entities.models.category import Category
from app.api.v1.domains.entities.models.entity_type import EntityType
from app.api.v1.domains.entities.models.entity_relation import EntityRelation
from app.api.v1.domains.entities.enums import CategoryName, EntityTypeName, RelationType


class TestEntityService:
    """Unit tests for EntityService."""

    def _seed_deps(self, db: Session) -> dict:
        """Create required Category and EntityType and return IDs."""
        from app.api.v1.domains.entities.services import entity as entity_service
        from app.api.v1.domains.entities.schemas.entity import EntityCreate

        category = Category(name=CategoryName.MYTH, description="A myth")
        entity_type = EntityType(name=EntityTypeName.CHARACTER, description="A character")
        db.add_all([category, entity_type])
        db.commit()
        return {"category_id": category.id, "entity_type_id": entity_type.id}

    def test_create_entity(self, db: Session):
        """Test creating an entity."""
        from app.api.v1.domains.entities.services import entity as entity_service
        from app.api.v1.domains.entities.schemas.entity import EntityCreate

        deps = self._seed_deps(db)
        entity_in = EntityCreate(
            name="Zeus",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
            description="King of the gods",
            is_active=True,
        )
        created = entity_service.create(db, obj_in=entity_in)

        assert created.name == "Zeus"
        assert created.description == "King of the gods"
        assert created.is_active is True
        assert created.id is not None

    def test_get_entity(self, db: Session):
        """Test getting an entity by ID."""
        from app.api.v1.domains.entities.services import entity as entity_service

        deps = self._seed_deps(db)
        entity = Entity(
            name="Mount Olympus",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
            description="Home of the gods",
            is_active=True,
        )
        db.add(entity)
        db.commit()

        retrieved = entity_service.get(db, item_id=entity.id)

        assert retrieved is not None
        assert retrieved.name == "Mount Olympus"

    def test_get_entity_not_found(self, db: Session):
        """Test getting a non-existent entity."""
        from app.api.v1.domains.entities.services import entity as entity_service

        retrieved = entity_service.get(db, item_id=999)
        assert retrieved is None

    def test_update_entity(self, db: Session):
        """Test updating an entity."""
        from app.api.v1.domains.entities.services import entity as entity_service
        from app.api.v1.domains.entities.schemas.entity import EntityCreate, EntityUpdate

        deps = self._seed_deps(db)
        entity_in = EntityCreate(
            name="Mjolnir",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        entity = entity_service.create(db, obj_in=entity_in)

        update_in = EntityUpdate(description="Thor's hammer")
        updated = entity_service.update(db, db_obj=entity, obj_in=update_in)

        assert updated.description == "Thor's hammer"

    def test_delete_entity(self, db: Session):
        """Test deleting an entity."""
        from app.api.v1.domains.entities.services import entity as entity_service

        deps = self._seed_deps(db)
        entity = Entity(
            name="To Delete",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()
        entity_id = entity.id

        entity_service.remove(db, item_id=entity_id)

        deleted = entity_service.get(db, item_id=entity_id)
        assert deleted is None

    def test_search_entities(self, db: Session):
        """Test searching entities by name, description, or origin."""
        from app.api.v1.domains.entities.services import entity as entity_service

        deps = self._seed_deps(db)
        entities = [
            Entity(name="Zeus", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], description="Greek god"),
            Entity(name="Hades", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], description="God of underworld"),
            Entity(name="Anubis", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], description="Egyptian deity"),
        ]
        db.add_all(entities)
        db.commit()

        results = entity_service.search(db, term="god")
        assert len(results) == 2

    def test_search_entities_no_results(self, db: Session):
        """Test search returning no results."""
        from app.api.v1.domains.entities.services import entity as entity_service

        deps = self._seed_deps(db)
        entity = Entity(name="Zeus", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"])
        db.add(entity)
        db.commit()

        results = entity_service.search(db, term="nonexistent")
        assert len(results) == 0

    def test_get_multi_with_filters(self, db: Session):
        """Test getting multiple entities with filters."""
        from app.api.v1.domains.entities.services import entity as entity_service

        myth = Category(name=CategoryName.MYTH)
        legend = Category(name=CategoryName.LEGEND)
        character = EntityType(name=EntityTypeName.CHARACTER)
        place = EntityType(name=EntityTypeName.PLACE)
        db.add_all([myth, legend, character, place])
        db.commit()

        entities = [
            Entity(name="Zeus", category_id=myth.id, entity_type_id=character.id, is_active=True),
            Entity(name="Mount Olympus", category_id=legend.id, entity_type_id=place.id, is_active=True),
            Entity(name="Inactive Entity", category_id=myth.id, entity_type_id=character.id, is_active=False),
        ]
        db.add_all(entities)
        db.commit()

        active_only = entity_service.get_multi(db, is_active=True)
        assert len(active_only) == 2


class TestEntitiesEndpoints:
    """Integration tests for Entities endpoints."""

    def _seed_dependencies(self, db: Session) -> dict:
        """Create required Category and EntityType records and return their IDs."""
        category = Category(name=CategoryName.MYTH, description="A myth category")
        entity_type = EntityType(name=EntityTypeName.CHARACTER, description="A character type")
        db.add_all([category, entity_type])
        db.commit()
        return {"category_id": category.id, "entity_type_id": entity_type.id}

    def test_list_entities_empty(self, client: TestClient):
        """Test listing entities when database is empty."""
        response = client.get("/api/v1/entities/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20

    def test_list_entities(self, client: TestClient, db: Session):
        """Test listing entities with data."""
        deps = self._seed_dependencies(db)

        entities = [
            Entity(name="Zeus", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], is_active=True),
            Entity(name="Hades", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], is_active=True),
        ]
        db.add_all(entities)
        db.commit()

        response = client.get("/api/v1/entities/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        names = {item["name"] for item in data["items"]}
        assert "Zeus" in names
        assert "Hades" in names

    def test_list_entities_pagination(self, client: TestClient, db: Session):
        """Test pagination parameters."""
        deps = self._seed_dependencies(db)

        for i in range(5):
            db.add(Entity(
                name=f"Entity {i}",
                category_id=deps["category_id"],
                entity_type_id=deps["entity_type_id"],
                is_active=True,
            ))
        db.commit()

        # Pagination is real DB-level pagination now: `total` must reflect
        # the full row count, not just the current page's size.
        response = client.get("/api/v1/entities/?page=1&size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1

    def test_list_entities_pagination_second_page_returns_remaining_rows(
        self, client: TestClient, db: Session
    ):
        """Regression test for the double-pagination bug: requesting page 2
        of a multi-page result set used to return an empty `items` list and
        a `total` equal to the page size (not the real row count), because
        the endpoint re-paginated a list that the DB query had already
        sliced to a single page. Page 2 of 45 rows at size=20 must return
        the 20 remaining rows (21-40) and `total` must be the real count."""
        deps = self._seed_dependencies(db)

        total_rows = 45
        for i in range(total_rows):
            db.add(Entity(
                name=f"Entity {i:03d}",
                category_id=deps["category_id"],
                entity_type_id=deps["entity_type_id"],
                is_active=True,
            ))
        db.commit()

        response = client.get("/api/v1/entities/?page=2&size=20")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == total_rows
        assert len(data["items"]) > 0
        assert len(data["items"]) == 20
        assert data["page"] == 2

    def test_list_entities_filter_by_entity_type(self, client: TestClient, db: Session):
        """Test filtering entities by entity_type."""
        myth = Category(name=CategoryName.MYTH)
        character = EntityType(name=EntityTypeName.CHARACTER)
        place = EntityType(name=EntityTypeName.PLACE)
        db.add_all([myth, character, place])
        db.commit()

        db.add_all([
            Entity(name="Zeus", category_id=myth.id, entity_type_id=character.id),
            Entity(name="Mount Olympus", category_id=myth.id, entity_type_id=place.id),
        ])
        db.commit()

        response = client.get("/api/v1/entities/?entity_type=CHARACTER")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Zeus"

    def test_list_entities_filter_by_category(self, client: TestClient, db: Session):
        """Test filtering entities by category."""
        myth = Category(name=CategoryName.MYTH)
        legend = Category(name=CategoryName.LEGEND)
        character = EntityType(name=EntityTypeName.CHARACTER)
        db.add_all([myth, legend, character])
        db.commit()

        db.add_all([
            Entity(name="Zeus", category_id=myth.id, entity_type_id=character.id),
            Entity(name="Beowulf", category_id=legend.id, entity_type_id=character.id),
        ])
        db.commit()

        response = client.get("/api/v1/entities/?category=LEGEND")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Beowulf"

    def test_list_entities_filter_by_is_active(self, client: TestClient, db: Session):
        """Test filtering entities by is_active status."""
        deps = self._seed_dependencies(db)

        db.add_all([
            Entity(name="Active Entity", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], is_active=True),
            Entity(name="Inactive Entity", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], is_active=False),
        ])
        db.commit()

        response = client.get("/api/v1/entities/?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Inactive Entity"

    def test_list_entities_default_is_active_true(self, client: TestClient, db: Session):
        """Test that is_active defaults to true filter."""
        deps = self._seed_dependencies(db)

        db.add_all([
            Entity(name="Active Entity", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], is_active=True),
            Entity(name="Inactive Entity", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], is_active=False),
        ])
        db.commit()

        response = client.get("/api/v1/entities/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Active Entity"

    def test_search_entities(self, client: TestClient, db: Session):
        """Test searching entities by name, description, or origin."""
        deps = self._seed_dependencies(db)

        db.add_all([
            Entity(name="Zeus", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], description="Greek god"),
            Entity(name="Hades", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], description="God of underworld"),
            Entity(name="Anubis", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], description="Egyptian deity"),
        ])
        db.commit()

        response = client.get("/api/v1/entities/search?q=god")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_search_entities_by_name(self, client: TestClient, db: Session):
        """Test searching entities by name."""
        deps = self._seed_dependencies(db)

        db.add_all([
            Entity(name="Zeus", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"]),
            Entity(name="Hades", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"]),
        ])
        db.commit()

        response = client.get("/api/v1/entities/search?q=Zeus")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Zeus"

    def test_search_entities_by_origin(self, client: TestClient, db: Session):
        """Test searching entities by origin field."""
        deps = self._seed_dependencies(db)

        db.add_all([
            Entity(name="Zeus", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], origin="Born on Mount Olympus"),
            Entity(name="Hades", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"], origin="Born in the underworld"),
        ])
        db.commit()

        response = client.get("/api/v1/entities/search?q=Mount Olympus")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Zeus"

    def test_search_entities_empty_query(self, client: TestClient):
        """Test that search with empty query returns 422."""
        response = client.get("/api/v1/entities/search?q=")
        assert response.status_code == 422

    def test_get_entity_by_id(self, client: TestClient, db: Session):
        """Test getting an entity by ID with relations."""
        deps = self._seed_dependencies(db)

        entity = Entity(
            name="Zeus",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
            description="King of the gods",
            origin="Born from Cronus and Rhea",
            is_active=True,
        )
        db.add(entity)
        db.commit()

        response = client.get(f"/api/v1/entities/{entity.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Zeus"
        assert data["description"] == "King of the gods"
        assert data["origin"] == "Born from Cronus and Rhea"
        assert data["category"]["name"] == CategoryName.MYTH
        assert data["entity_type"]["name"] == EntityTypeName.CHARACTER
        assert "relations" in data

    def test_get_entity_not_found(self, client: TestClient):
        """Test getting a non-existent entity."""
        response = client.get("/api/v1/entities/999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Entity not found"

    def test_create_entity(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test creating an entity."""
        deps = self._seed_dependencies(db)

        response = client.post(
            "/api/v1/entities/",
            headers=superuser_headers,
            json={
                "name": "Poseidon",
                "category_id": deps["category_id"],
                "entity_type_id": deps["entity_type_id"],
                "description": "God of the sea",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Poseidon"
        assert data["description"] == "God of the sea"
        assert data["is_active"] is True

    def test_create_entity_minimal(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test creating an entity with only required fields."""
        deps = self._seed_dependencies(db)

        response = client.post(
            "/api/v1/entities/",
            headers=superuser_headers,
            json={
                "name": "Minimal Entity",
                "category_id": deps["category_id"],
                "entity_type_id": deps["entity_type_id"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Entity"
        assert data["is_active"] is True

    def test_update_entity(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test updating an entity."""
        deps = self._seed_dependencies(db)

        entity = Entity(
            name="Original Name",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.put(
            f"/api/v1/entities/{entity.id}",
            headers=superuser_headers,
            json={"name": "Updated Name", "description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    def test_update_entity_not_found(self, client: TestClient, superuser_headers: dict):
        """Test updating a non-existent entity."""
        response = client.put(
            "/api/v1/entities/999",
            headers=superuser_headers,
            json={"name": "Does Not Exist"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Entity not found"

    def test_update_entity_partial(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test partial update of an entity."""
        deps = self._seed_dependencies(db)

        entity = Entity(
            name="Original",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
            description="Original description",
        )
        db.add(entity)
        db.commit()

        response = client.put(
            f"/api/v1/entities/{entity.id}",
            headers=superuser_headers,
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original"
        assert data["description"] == "Original description"
        assert data["is_active"] is False

    def test_delete_entity(self, client: TestClient, db: Session, superuser_headers: dict):
        """Test deleting an entity."""
        deps = self._seed_dependencies(db)

        entity = Entity(
            name="To Delete",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.delete(f"/api/v1/entities/{entity.id}", headers=superuser_headers)
        assert response.status_code == 204

        response = client.get(f"/api/v1/entities/{entity.id}")
        assert response.status_code == 404

    def test_delete_entity_not_found(self, client: TestClient, superuser_headers: dict):
        """Test deleting a non-existent entity."""
        response = client.delete("/api/v1/entities/999", headers=superuser_headers)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Entity not found"

    def test_create_entity_without_auth(self, client: TestClient, db: Session):
        """Test creating an entity without authentication returns 401."""
        deps = self._seed_dependencies(db)

        response = client.post(
            "/api/v1/entities/",
            json={
                "name": "Unauthorized Entity",
                "category_id": deps["category_id"],
                "entity_type_id": deps["entity_type_id"],
            },
        )
        assert response.status_code == 401

    def test_create_entity_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test creating an entity as non-superuser returns 403."""
        deps = self._seed_dependencies(db)

        response = client.post(
            "/api/v1/entities/",
            headers=auth_headers,
            json={
                "name": "Forbidden Entity",
                "category_id": deps["category_id"],
                "entity_type_id": deps["entity_type_id"],
            },
        )
        assert response.status_code == 403

    def test_update_entity_without_auth(self, client: TestClient, db: Session):
        """Test updating an entity without authentication returns 401."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Original",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.put(
            f"/api/v1/entities/{entity.id}",
            json={"name": "Hacked"},
        )
        assert response.status_code == 401

    def test_update_entity_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test updating an entity as non-superuser returns 403."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Original",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.put(
            f"/api/v1/entities/{entity.id}",
            headers=auth_headers,
            json={"name": "Hacked"},
        )
        assert response.status_code == 403

    def test_delete_entity_without_auth(self, client: TestClient, db: Session):
        """Test deleting an entity without authentication returns 401."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="To Delete",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.delete(f"/api/v1/entities/{entity.id}")
        assert response.status_code == 401

    def test_delete_entity_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test deleting an entity as non-superuser returns 403."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="To Delete",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.delete(f"/api/v1/entities/{entity.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_get_entity_relations(self, client: TestClient, db: Session):
        """Test getting entity relations."""
        deps = self._seed_dependencies(db)

        entity1 = Entity(
            name="Zeus",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        entity2 = Entity(
            name="Hades",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add_all([entity1, entity2])
        db.commit()

        relation = EntityRelation(
            entity_origin_id=entity1.id,
            entity_destination_id=entity2.id,
            relation_type=RelationType.SIBLINGS,
            description="Brothers",
        )
        db.add(relation)
        db.commit()

        response = client.get(f"/api/v1/entities/{entity1.id}/relations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["relation_type"] == "SIBLINGS"
        assert data[0]["related_entity_id"] == entity2.id
        assert data[0]["related_entity_name"] == "Hades"
        assert data[0]["direction"] == "origin"
        assert data[0]["description"] == "Brothers"

    def test_get_entity_relations_as_destination(self, client: TestClient, db: Session):
        """Test getting relations where entity is the destination."""
        deps = self._seed_dependencies(db)

        entity1 = Entity(
            name="Zeus",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        entity2 = Entity(
            name="Hades",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add_all([entity1, entity2])
        db.commit()

        relation = EntityRelation(
            entity_origin_id=entity1.id,
            entity_destination_id=entity2.id,
            relation_type=RelationType.SIBLINGS,
        )
        db.add(relation)
        db.commit()

        response = client.get(f"/api/v1/entities/{entity2.id}/relations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["direction"] == "destination"

    def test_get_entity_relations_empty(self, client: TestClient, db: Session):
        """Test getting relations for entity with no relations."""
        deps = self._seed_dependencies(db)

        entity = Entity(
            name="Lone Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.get(f"/api/v1/entities/{entity.id}/relations")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_entity_relations_not_found(self, client: TestClient):
        """Test getting relations for non-existent entity."""
        response = client.get("/api/v1/entities/999/relations")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Entity not found"

    def test_get_entity_by_id_includes_relations(self, client: TestClient, db: Session):
        """Test that get entity includes relations in response."""
        deps = self._seed_dependencies(db)

        entity1 = Entity(
            name="Zeus",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        entity2 = Entity(
            name="Ares",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add_all([entity1, entity2])
        db.commit()

        db.add(EntityRelation(
            entity_origin_id=entity1.id,
            entity_destination_id=entity2.id,
            relation_type=RelationType.FATHER_CHILD,
        ))
        db.commit()

        response = client.get(f"/api/v1/entities/{entity1.id}")
        assert response.status_code == 200
        data = response.json()
        assert "relations" in data
        assert len(data["relations"]) == 1
        assert data["relations"][0]["relation_type"] == "FATHER_CHILD"

    def test_create_relation(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test creating a relation between two entities as superuser."""
        deps = self._seed_dependencies(db)
        origin = Entity(
            name="Origin Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        destination = Entity(
            name="Destination Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add_all([origin, destination])
        db.commit()

        response = client.post(
            f"/api/v1/entities/{origin.id}/relations",
            json={
                "entity_destination_id": destination.id,
                "relation_type": "ENEMIES",
                "description": "Test rivalry",
            },
            headers=superuser_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["relation_type"] == "ENEMIES"
        assert data["description"] == "Test rivalry"
        assert data["entity_origin_name"] == "Origin Entity"
        assert data["entity_destination_name"] == "Destination Entity"

        # ENEMIES is symmetric — verify the reverse relation was also created,
        # and that the description was carried over to it too.
        reverse_check = client.get(f"/api/v1/entities/{destination.id}/relations")
        assert reverse_check.status_code == 200
        reverse_data = reverse_check.json()
        assert any(
            r["relation_type"] == "ENEMIES" and r["description"] == "Test rivalry"
            for r in reverse_data
        )

    def test_create_relation_entity_not_found(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test creating a relation from a non-existent entity returns 404."""
        response = client.post(
            "/api/v1/entities/99999/relations",
            json={"entity_destination_id": 1, "relation_type": "ALLIES"},
            headers=superuser_headers,
        )
        assert response.status_code == 404

    def test_create_relation_destination_not_found(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """A relation to a non-existent destination returns 404 (origin exists)."""
        deps = self._seed_dependencies(db)
        origin = Entity(
            name="Origin Only",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(origin)
        db.commit()

        response = client.post(
            f"/api/v1/entities/{origin.id}/relations",
            json={"entity_destination_id": 99999, "relation_type": "ALLIES"},
            headers=superuser_headers,
        )
        assert response.status_code == 404

    def test_create_relation_without_auth(self, client: TestClient, db: Session):
        """Test creating a relation without auth returns 401."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Some Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.post(
            f"/api/v1/entities/{entity.id}/relations",
            json={"entity_destination_id": entity.id, "relation_type": "ALLIES"},
        )
        assert response.status_code == 401

    def test_create_relation_as_regular_user(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test creating a relation as non-superuser returns 403."""
        deps = self._seed_dependencies(db)
        origin = Entity(
            name="Origin Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        destination = Entity(
            name="Destination Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add_all([origin, destination])
        db.commit()

        response = client.post(
            f"/api/v1/entities/{origin.id}/relations",
            json={
                "entity_destination_id": destination.id,
                "relation_type": "ENEMIES",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_relation_to_self_rejected(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test creating a relation from an entity to itself returns 400,
        rather than an unhandled 500 from the unique-constraint collision
        between the forward and reverse rows of a symmetric relation."""
        deps = self._seed_dependencies(db)
        entity = Entity(
            name="Solo Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.post(
            f"/api/v1/entities/{entity.id}/relations",
            json={"entity_destination_id": entity.id, "relation_type": "SIBLINGS"},
            headers=superuser_headers,
        )
        assert response.status_code == 400

    def test_create_relation_to_self_nonexistent_origin_returns_404(
        self, client: TestClient, superuser_headers: dict
    ):
        """Test that a self-relation against a nonexistent origin entity
        reports 404 (entity not found), not 400 (self-relation) — existence
        must be checked before the self-relation guard."""
        response = client.post(
            "/api/v1/entities/999999/relations",
            json={"entity_destination_id": 999999, "relation_type": "SIBLINGS"},
            headers=superuser_headers,
        )
        assert response.status_code == 404

    def test_create_duplicate_relation_returns_409(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        """Test that creating the same (origin, destination, relation_type)
        relation twice returns 409, rather than an unhandled 500 from the
        uq_entity_relation_unique constraint."""
        deps = self._seed_dependencies(db)
        origin = Entity(
            name="Origin Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        destination = Entity(
            name="Destination Entity",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add_all([origin, destination])
        db.commit()

        payload = {
            "entity_destination_id": destination.id,
            "relation_type": "ALLIES",
        }
        first = client.post(
            f"/api/v1/entities/{origin.id}/relations",
            json=payload,
            headers=superuser_headers,
        )
        assert first.status_code == 201

        second = client.post(
            f"/api/v1/entities/{origin.id}/relations",
            json=payload,
            headers=superuser_headers,
        )
        assert second.status_code == 409


class TestEntitiesListSorting:
    """sort/order are validated and applied before pagination (issue #54)."""

    URL = "/api/v1/entities/"

    @pytest.fixture
    def entities(self, db: Session) -> None:
        from datetime import datetime

        category = Category(name=CategoryName.MYTH, description="A myth")
        entity_type = EntityType(name=EntityTypeName.CHARACTER, description="A character")
        db.add_all([category, entity_type])
        db.commit()
        # Insert order (id) differs from both name order and created_at order.
        for name, day in [("Cyclops", 2), ("Anubis", 3), ("Bastet", 1)]:
            db.add(
                Entity(
                    name=name,
                    category_id=category.id,
                    entity_type_id=entity_type.id,
                    is_active=True,
                    created_at=datetime(2026, 1, day),
                )
            )
        db.commit()

    def _all_names(self, client, **params):
        """Walk every page (size=2) so ordering is proven across pages."""
        names, page = [], 1
        while True:
            response = client.get(self.URL, params={"size": 2, "page": page, **params})
            assert response.status_code == 200
            items = response.json()["items"]
            if not items:
                return names
            names += [e["name"] for e in items]
            page += 1

    @pytest.mark.parametrize(
        "sort, order, expected",
        [
            ("name", "asc", ["Anubis", "Bastet", "Cyclops"]),
            ("name", "desc", ["Cyclops", "Bastet", "Anubis"]),
            ("id", "asc", ["Cyclops", "Anubis", "Bastet"]),
            ("id", "desc", ["Bastet", "Anubis", "Cyclops"]),
            ("created_at", "asc", ["Bastet", "Cyclops", "Anubis"]),
            ("created_at", "desc", ["Anubis", "Cyclops", "Bastet"]),
        ],
    )
    def test_should_order_across_pages(self, client, entities, sort, order, expected):
        assert self._all_names(client, sort=sort, order=order) == expected

    def test_should_default_to_name_ascending(self, client, entities):
        assert self._all_names(client) == ["Anubis", "Bastet", "Cyclops"]

    @pytest.mark.parametrize(
        "params",
        [
            {"sort": "description"},
            {"sort": "__class__"},
            {"sort": "is_active"},
            {"order": "sideways"},
            {"order": "DESC"},
        ],
    )
    def test_should_reject_values_outside_allowed_set(self, client, params):
        assert client.get(self.URL, params=params).status_code == 422


def _seed_entities(db: Session, count: int = 2) -> list[Entity]:
    """Create the category/type dependencies and `count` entities."""
    category = Category(name=CategoryName.MYTH, description="A myth")
    entity_type = EntityType(name=EntityTypeName.CHARACTER, description="A character")
    db.add_all([category, entity_type])
    db.commit()
    entities = [
        Entity(
            name=f"Relation Entity {i}",
            category_id=category.id,
            entity_type_id=entity_type.id,
        )
        for i in range(count)
    ]
    db.add_all(entities)
    db.commit()
    return entities


SYMMETRIC_TYPES = [RelationType.SIBLINGS, RelationType.ALLIES, RelationType.ENEMIES]
DIRECTED_TYPES = [
    RelationType.MOTHER_CHILD,
    RelationType.FATHER_CHILD,
    RelationType.GUARDIAN_PLACE,
]


class TestSymmetricRelationTypes:
    """The symmetric-type list has one definition shared by create and delete."""

    def test_constant_holds_exactly_the_symmetric_types(self):
        from app.api.v1.domains.entities.enums import SYMMETRIC_RELATION_TYPES

        assert SYMMETRIC_RELATION_TYPES == set(SYMMETRIC_TYPES)

    @pytest.mark.parametrize("relation_type", SYMMETRIC_TYPES + DIRECTED_TYPES)
    def test_create_stores_a_pair_only_for_symmetric_types(
        self, db: Session, relation_type: RelationType
    ):
        origin, destination = _seed_entities(db)
        _forward, reverse = _create_relation(db, origin, destination, relation_type)

        expected_rows = 2 if relation_type in SYMMETRIC_TYPES else 1
        assert db.query(EntityRelation).count() == expected_rows
        assert (reverse is not None) == (relation_type in SYMMETRIC_TYPES)


def _create_relation(db: Session, origin, destination, relation_type):
    from app.api.v1.domains.entities.services import relation as relation_service

    forward, reverse = relation_service.create_bidirectional(
        db,
        origin_id=origin.id,
        destination_id=destination.id,
        relation_type=relation_type,
    )
    return forward, reverse


class TestEntityRelationDeleteService:
    """Unit tests for EntityRelationService.get_for_entity / remove_with_reverse."""

    def test_get_for_entity_finds_relation_by_origin(self, db: Session):
        from app.api.v1.domains.entities.services import relation as relation_service

        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        found = relation_service.get_for_entity(
            db, entity_id=a.id, relation_id=forward.id
        )
        assert found is not None and found.id == forward.id

    def test_get_for_entity_finds_relation_by_destination(self, db: Session):
        from app.api.v1.domains.entities.services import relation as relation_service

        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        found = relation_service.get_for_entity(
            db, entity_id=b.id, relation_id=forward.id
        )
        assert found is not None and found.id == forward.id

    def test_get_for_entity_returns_none_for_foreign_or_missing_relation(
        self, db: Session
    ):
        from app.api.v1.domains.entities.services import relation as relation_service

        a, b, c = _seed_entities(db, 3)
        forward, _ = _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        assert (
            relation_service.get_for_entity(db, entity_id=c.id, relation_id=forward.id)
            is None
        )
        assert (
            relation_service.get_for_entity(db, entity_id=a.id, relation_id=999999)
            is None
        )

    @pytest.mark.parametrize("relation_type", SYMMETRIC_TYPES)
    def test_remove_with_reverse_deletes_both_rows_of_a_symmetric_relation(
        self, db: Session, relation_type: RelationType
    ):
        from app.api.v1.domains.entities.services import relation as relation_service

        a, b = _seed_entities(db)
        forward, reverse = _create_relation(db, a, b, relation_type)
        relation_service.remove_with_reverse(db, relation=reverse)
        db.expire_all()
        assert db.query(EntityRelation).count() == 0
        assert db.get(Entity, a.id) is not None and db.get(Entity, b.id) is not None

    @pytest.mark.parametrize("relation_type", DIRECTED_TYPES)
    def test_remove_with_reverse_deletes_only_the_row_of_a_directed_relation(
        self, db: Session, relation_type: RelationType
    ):
        from app.api.v1.domains.entities.services import relation as relation_service

        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, relation_type)
        # An opposite-direction row of the same type is a different relation.
        other, _ = _create_relation(db, b, a, relation_type)
        relation_service.remove_with_reverse(db, relation=forward)
        db.expire_all()
        assert [r.id for r in db.query(EntityRelation).all()] == [other.id]

    def test_remove_with_reverse_tolerates_a_missing_reverse_row(self, db: Session):
        from app.api.v1.domains.entities.services import relation as relation_service

        a, b = _seed_entities(db)
        forward, reverse = _create_relation(db, a, b, RelationType.ALLIES)
        db.delete(reverse)
        db.commit()
        relation_service.remove_with_reverse(db, relation=forward)
        assert db.query(EntityRelation).count() == 0

    def test_remove_with_reverse_rolls_back_and_reraises_when_the_commit_fails(
        self, db: Session, monkeypatch
    ):
        """Both deletes share one commit, so a failing commit must roll back
        and surface the error. (Row counts can't be asserted here: the test
        session sits inside an outer transaction that rollback also undoes.)"""
        from sqlalchemy.exc import SQLAlchemyError

        from app.api.v1.domains.entities.services import relation as relation_service

        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.SIBLINGS)
        rollbacks = []

        def failing_commit():
            raise SQLAlchemyError("boom")

        monkeypatch.setattr(db, "commit", failing_commit)
        monkeypatch.setattr(db, "rollback", lambda: rollbacks.append(True))
        with pytest.raises(SQLAlchemyError):
            relation_service.remove_with_reverse(db, relation=forward)

        assert rollbacks == [True]

    def test_remove_with_reverse_leaves_other_types_between_the_pair(
        self, db: Session
    ):
        from app.api.v1.domains.entities.services import relation as relation_service

        a, b = _seed_entities(db)
        sib, _ = _create_relation(db, a, b, RelationType.SIBLINGS)
        enemies, enemies_rev = _create_relation(db, a, b, RelationType.ENEMIES)
        relation_service.remove_with_reverse(db, relation=sib)
        db.expire_all()
        assert {r.id for r in db.query(EntityRelation).all()} == {
            enemies.id,
            enemies_rev.id,
        }


class TestDeleteEntityRelationEndpoint:
    """DELETE /entities/{id}/relations/{relation_id}."""

    def _url(self, entity_id: int, relation_id: int) -> str:
        return f"/api/v1/entities/{entity_id}/relations/{relation_id}"

    def _listed_ids(self, client: TestClient, entity_id: int) -> list[int]:
        response = client.get(f"/api/v1/entities/{entity_id}/relations")
        assert response.status_code == 200
        return [r["id"] for r in response.json()]

    def test_delete_relation_removes_a_directed_relation(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.FATHER_CHILD)

        response = client.delete(self._url(a.id, forward.id), headers=superuser_headers)

        assert response.status_code == 204
        assert response.content == b""
        assert self._listed_ids(client, a.id) == []
        assert self._listed_ids(client, b.id) == []
        assert client.get(f"/api/v1/entities/{a.id}").status_code == 200
        assert client.get(f"/api/v1/entities/{b.id}").status_code == 200

    @pytest.mark.parametrize("relation_type", SYMMETRIC_TYPES)
    @pytest.mark.parametrize("via", ["forward_from_origin", "reverse_from_destination"])
    def test_delete_relation_removes_both_rows_of_a_symmetric_relation(
        self,
        client: TestClient,
        db: Session,
        superuser_headers: dict,
        via: str,
        relation_type: RelationType,
    ):
        a, b = _seed_entities(db)
        forward, reverse = _create_relation(db, a, b, relation_type)
        entity_id, relation_id = (
            (a.id, forward.id)
            if via == "forward_from_origin"
            else (b.id, reverse.id)
        )

        response = client.delete(
            self._url(entity_id, relation_id), headers=superuser_headers
        )

        assert response.status_code == 204
        assert self._listed_ids(client, a.id) == []
        assert self._listed_ids(client, b.id) == []

    def test_delete_relation_via_destination_path_uses_the_listed_id(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        a, b = _seed_entities(db)
        _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        listed = self._listed_ids(client, b.id)
        assert len(listed) == 1

        response = client.delete(self._url(b.id, listed[0]), headers=superuser_headers)

        assert response.status_code == 204
        assert self._listed_ids(client, a.id) == []

    def test_delete_relation_twice_returns_404_the_second_time(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        url = self._url(a.id, forward.id)
        assert client.delete(url, headers=superuser_headers).status_code == 204
        second = client.delete(url, headers=superuser_headers)
        assert second.status_code == 404
        assert second.json()["detail"] == "Relation not found"


class TestDeleteEntityRelationErrors:
    """Error contract of DELETE /entities/{id}/relations/{relation_id}."""

    def _url(self, entity_id: int, relation_id: int) -> str:
        return f"/api/v1/entities/{entity_id}/relations/{relation_id}"

    def test_delete_relation_without_token_returns_401(
        self, client: TestClient, db: Session
    ):
        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        assert client.delete(self._url(a.id, forward.id)).status_code == 401
        assert db.query(EntityRelation).count() == 1

    def test_delete_relation_as_regular_user_returns_403_without_deleting(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        response = client.delete(self._url(a.id, forward.id), headers=auth_headers)
        assert response.status_code == 403
        assert db.query(EntityRelation).count() == 1

    def test_delete_relation_as_regular_user_does_not_reveal_existence(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        a, b = _seed_entities(db)
        forward, _ = _create_relation(db, a, b, RelationType.MOTHER_CHILD)
        existing = client.delete(self._url(a.id, forward.id), headers=auth_headers)
        missing = client.delete(self._url(999999, 999999), headers=auth_headers)
        assert existing.status_code == missing.status_code == 403
        assert existing.json() == missing.json()

    def test_delete_relation_of_missing_entity_returns_404(
        self, client: TestClient, superuser_headers: dict
    ):
        response = client.delete(self._url(999999, 1), headers=superuser_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Entity not found"

    def test_delete_missing_and_foreign_relations_return_the_same_404(
        self, client: TestClient, db: Session, superuser_headers: dict
    ):
        a, b, c = _seed_entities(db, 3)
        forward, _ = _create_relation(db, a, b, RelationType.SIBLINGS)

        foreign = client.delete(self._url(c.id, forward.id), headers=superuser_headers)
        missing = client.delete(self._url(a.id, 999999), headers=superuser_headers)

        assert foreign.status_code == missing.status_code == 404
        assert foreign.json() == missing.json() == {"detail": "Relation not found"}
        assert db.query(EntityRelation).count() == 2  # nothing was deleted

    @pytest.mark.parametrize("entity_id,relation_id", [(0, 1), (1, 0), (-1, 1), (1, -1)])
    def test_delete_relation_rejects_non_positive_ids(
        self, client: TestClient, superuser_headers: dict, entity_id, relation_id
    ):
        response = client.delete(
            self._url(entity_id, relation_id), headers=superuser_headers
        )
        assert response.status_code == 422

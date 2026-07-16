"""
Tests for Entities domain.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.entities.models.entity import Entity
from app.api.v1.entities.models.category import Category
from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.models.entity_relation import EntityRelation
from app.api.v1.entities.enums import CategoryName, EntityTypeName, RelationType


class TestEntityService:
    """Unit tests for EntityService."""

    def _seed_deps(self, db: Session) -> dict:
        """Create required Category and EntityType and return IDs."""
        from app.api.v1.entities.services import entity as entity_service
        from app.api.v1.entities.schemas.entity import EntityCreate

        category = Category(name=CategoryName.MYTH, description="A myth")
        entity_type = EntityType(name=EntityTypeName.CHARACTER, description="A character")
        db.add_all([category, entity_type])
        db.commit()
        return {"category_id": category.id, "entity_type_id": entity_type.id}

    def test_create_entity(self, db: Session):
        """Test creating an entity."""
        from app.api.v1.entities.services import entity as entity_service
        from app.api.v1.entities.schemas.entity import EntityCreate

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
        from app.api.v1.entities.services import entity as entity_service

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
        from app.api.v1.entities.services import entity as entity_service

        retrieved = entity_service.get(db, item_id=999)
        assert retrieved is None

    def test_update_entity(self, db: Session):
        """Test updating an entity."""
        from app.api.v1.entities.services import entity as entity_service
        from app.api.v1.entities.schemas.entity import EntityCreate, EntityUpdate

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
        from app.api.v1.entities.services import entity as entity_service

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
        from app.api.v1.entities.services import entity as entity_service

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
        from app.api.v1.entities.services import entity as entity_service

        deps = self._seed_deps(db)
        entity = Entity(name="Zeus", category_id=deps["category_id"], entity_type_id=deps["entity_type_id"])
        db.add(entity)
        db.commit()

        results = entity_service.search(db, term="nonexistent")
        assert len(results) == 0

    def test_get_multi_with_filters(self, db: Session):
        """Test getting multiple entities with filters."""
        from app.api.v1.entities.services import entity as entity_service

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

        # Endpoint limits results before paginating, so total reflects the limited set
        response = client.get("/api/v1/entities/?page=1&size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1

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

    def test_create_entity(self, client: TestClient, db: Session):
        """Test creating an entity."""
        deps = self._seed_dependencies(db)

        response = client.post(
            "/api/v1/entities/",
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

    def test_create_entity_minimal(self, client: TestClient, db: Session):
        """Test creating an entity with only required fields."""
        deps = self._seed_dependencies(db)

        response = client.post(
            "/api/v1/entities/",
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

    def test_update_entity(self, client: TestClient, db: Session):
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
            json={"name": "Updated Name", "description": "New description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    def test_update_entity_not_found(self, client: TestClient):
        """Test updating a non-existent entity."""
        response = client.put(
            "/api/v1/entities/999",
            json={"name": "Does Not Exist"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Entity not found"

    def test_update_entity_partial(self, client: TestClient, db: Session):
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
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original"
        assert data["description"] == "Original description"
        assert data["is_active"] is False

    def test_delete_entity(self, client: TestClient, db: Session):
        """Test deleting an entity."""
        deps = self._seed_dependencies(db)

        entity = Entity(
            name="To Delete",
            category_id=deps["category_id"],
            entity_type_id=deps["entity_type_id"],
        )
        db.add(entity)
        db.commit()

        response = client.delete(f"/api/v1/entities/{entity.id}")
        assert response.status_code == 204

        response = client.get(f"/api/v1/entities/{entity.id}")
        assert response.status_code == 404

    def test_delete_entity_not_found(self, client: TestClient):
        """Test deleting a non-existent entity."""
        response = client.delete("/api/v1/entities/999")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Entity not found"

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

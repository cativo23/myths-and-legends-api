from app.api.v1.entities.models.category import Category
from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.models.entity import Entity
from app.api.v1.entities.models.characteristic import Characteristic
from app.api.v1.entities.models.location import Location
from app.api.v1.entities.models.entity_relation import EntityRelation
from app.api.v1.entities.models.source import Source

from app.api.v1.entities.services.category import CategoryService
from app.api.v1.entities.services.entity_type import EntityTypeService
from app.api.v1.entities.services.entity import EntityService
from app.api.v1.entities.services.characteristic import CharacteristicService
from app.api.v1.entities.services.location import LocationService
from app.api.v1.entities.services.entity_relation import EntityRelationService
from app.api.v1.entities.services.source import SourceService

# Service instances (singletons)
category = CategoryService(Category)
entity_type = EntityTypeService(EntityType)
entity = EntityService(Entity)
characteristic = CharacteristicService(Characteristic)
location = LocationService(Location)
relation = EntityRelationService(EntityRelation)
source = SourceService(Source)

__all__ = [
    "category",
    "entity_type",
    "entity",
    "characteristic",
    "location",
    "relation",
    "source",
    "CategoryService",
    "EntityTypeService",
    "EntityService",
    "CharacteristicService",
    "LocationService",
    "EntityRelationService",
    "SourceService",
]

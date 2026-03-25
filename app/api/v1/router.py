from fastapi import APIRouter

from app.api.v1.endpoints import home, login, users, countries, images
from app.api.v1.entities.endpoints import entities, locations, sources, categories, entity_types

api_router = APIRouter()

api_router.include_router(home.router, tags=["home"])
api_router.include_router(login.router, prefix="/auth", tags=["auth"])
api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
api_router.include_router(images.router, prefix="/images", tags=["images"])

# Entities API
api_router.include_router(entities.router)  # prefix="/entities"
api_router.include_router(locations.router)  # prefix="/locations"
api_router.include_router(sources.router)  # prefix="/sources"
api_router.include_router(categories.router)  # prefix="/categories"
api_router.include_router(entity_types.router)  # prefix="/entity-types"

# api_router.include_router(users.router, prefix="/users", tags=["users"])

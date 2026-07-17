from fastapi import APIRouter

from app.api.v1.domains.home.endpoints.home import router as home_router
from app.api.v1.domains.auth.endpoints.auth import router as auth_router
from app.api.v1.domains.countries.endpoints.countries import router as countries_router
from app.api.v1.domains.users.endpoints.users import router as users_router
from app.api.v1.domains.images.endpoints.images import router as images_router
from app.api.v1.domains.health.endpoints.health import router as health_router
from app.api.v1.domains.entities.endpoints import (
    entities,
    locations,
    sources,
    categories,
    entity_types,
)

api_router = APIRouter()

api_router.include_router(home_router, tags=["home"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(countries_router, prefix="/countries", tags=["countries"])
api_router.include_router(images_router, prefix="/images", tags=["images"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(health_router, tags=["health"])

# Entities API
api_router.include_router(entities.router)  # prefix="/entities"
api_router.include_router(locations.router)  # prefix="/locations"
api_router.include_router(sources.router)  # prefix="/sources"
api_router.include_router(categories.router)  # prefix="/categories"
api_router.include_router(entity_types.router)  # prefix="/entity-types"

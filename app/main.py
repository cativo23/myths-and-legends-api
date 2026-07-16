import logging
from typing import Any, Dict

from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

from app.api.common.exceptions.api_exception import add_exception_handler
from app.api.common.middleware import SecurityHeadersMiddleware, RequestIDMiddleware
from app.api.common.middleware.rate_limiter import setup_rate_limiter
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging, LoggingMiddleware
from app.core.openapi_config import get_public_openapi, get_admin_openapi
from fastapi_pagination import add_pagination

# Setup structured logging
setup_logging(level="INFO")

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
## Overview

The Myths and Legends API is a comprehensive REST API for managing mythological characters, creatures, places, and objects from various cultures and mythologies around the world.

## Features

- **Entities Management**: Browse mythological entities (characters, creatures, places, objects)
- **Countries**: Explore countries and their associated myths
- **Categories & Types**: Classify entities by category and mythological origin
- **Relations**: Discover relationships between entities
- **Characteristics**: Learn about powers, weaknesses, and physical features
- **Locations**: Explore geographic places associated with myths
- **Sources**: Reference original materials (books, manuscripts, oral traditions)
- **Rate Limiting**: Protection against brute force attacks
- **Security Headers**: Enhanced HTTP security headers

## Rate Limiting

- General endpoints: 60 requests per minute
- Authentication endpoints: 10 requests per minute

## Looking for Admin Documentation?

Admin endpoints (create, update, delete) are documented at `/admin/docs` (requires authentication).
    """,
    version="1.0.0",
    openapi_url=None,  # Disable default openapi.json
    docs_url=None,  # Disable default /docs
    redoc_url=None,  # Disable default /redoc
    contact={
        "name": "Carlos Cativo",
        "email": "cativo23.kt@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Starlette's add_middleware() inserts each new middleware at the FRONT of the
# user_middleware list, and build_middleware_stack() wraps that list in
# reversed order — so the LAST middleware registered ends up OUTERMOST and
# runs FIRST on the way in (closest to the client), while the FIRST middleware
# registered ends up INNERMOST and runs LAST on the way in (closest to the
# route). Actual execution order on a request, given the registrations below,
# is: CORS -> SecurityHeaders -> RequestID -> Logging -> route.

# Structured logging (innermost of this group; registered first so it runs
# last on the way in, after RequestID has set request.state.request_id)
app.add_middleware(LoggingMiddleware)

# Request ID (registered after Logging so it runs before Logging on the way
# in, ensuring request.state.request_id is set before Logging reads it)
app.add_middleware(RequestIDMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Set all CORS enabled (registered last so it runs first / outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=f"/api/v{settings.API_VERSION}")

add_pagination(app)

add_exception_handler(app)

# Rate limiting (must be last to wrap all other middleware)
setup_rate_limiter(app)


# Store the full unfiltered schema
_full_openapi_schema: Dict[str, Any] | None = None


def get_full_openapi() -> Dict[str, Any]:
    """Get the full unfiltered OpenAPI schema."""
    global _full_openapi_schema
    if _full_openapi_schema is None:
        _full_openapi_schema = app.openapi()
    return _full_openapi_schema


def custom_openapi_public() -> Dict[str, Any]:
    """Generate OpenAPI schema with only public endpoints."""
    full_schema = get_full_openapi()
    return get_public_openapi(full_schema)


def custom_openapi_admin() -> Dict[str, Any]:
    """Generate OpenAPI schema with only admin endpoints."""
    full_schema = get_full_openapi()
    return get_admin_openapi(full_schema)


# Public OpenAPI schema endpoint
@app.get(f"/api/v{settings.API_VERSION}/openapi.json", include_in_schema=False)
async def get_public_openapi_json():
    """Get public OpenAPI schema (only public endpoints)."""
    return custom_openapi_public()


# Admin OpenAPI schema endpoint
@app.get(f"/api/v{settings.API_VERSION}/openapi-admin.json", include_in_schema=False)
async def get_admin_openapi_json():
    """Get admin OpenAPI schema (only admin endpoints)."""
    return custom_openapi_admin()


# Public Swagger UI
@app.get("/docs", include_in_schema=False)
async def public_swagger_ui():
    """Public Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url=f"/api/v{settings.API_VERSION}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Public Docs",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# Admin Swagger UI
@app.get("/admin/docs", include_in_schema=False)
async def admin_swagger_ui():
    """Admin Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url=f"/api/v{settings.API_VERSION}/openapi-admin.json",
        title=f"{settings.PROJECT_NAME} - Admin Docs",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# Public ReDoc
@app.get("/redoc", include_in_schema=False)
async def public_redoc():
    """Public ReDoc documentation."""
    from fastapi.openapi.docs import get_redoc_html

    return get_redoc_html(
        openapi_url=f"/api/v{settings.API_VERSION}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Public Docs",
    )


# Admin ReDoc
@app.get("/admin/redoc", include_in_schema=False)
async def admin_redoc():
    """Admin ReDoc documentation."""
    from fastapi.openapi.docs import get_redoc_html

    return get_redoc_html(
        openapi_url=f"/api/v{settings.API_VERSION}/openapi-admin.json",
        title=f"{settings.PROJECT_NAME} - Admin Docs",
    )


@app.get("/")
def index():
    logger.info("Index endpoint called")
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "data": {
            "description": "This is the Myths and Legends API",
            "author": "Carlos Cativo <cativo23.kt@gmail.com>",
            "important-urls": [
                {"public_docs": f"{settings.SERVER_HOST}:{settings.APP_PORT}/docs"},
                {
                    "admin_docs": f"{settings.SERVER_HOST}:{settings.APP_PORT}/admin/docs"
                },
                {
                    "versions": {
                        "v1": f"{settings.SERVER_HOST}:{settings.APP_PORT}/api/v1"
                    }
                },
            ],
        },
    }

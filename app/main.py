import logging

from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.api.common.exceptions.api_exception import add_exception_handler
from app.api.common.middleware import SecurityHeadersMiddleware, RequestIDMiddleware
from app.api.common.middleware.rate_limiter import setup_rate_limiter
from app.api.common.middleware.request_id import (
    RequestIDMiddleware as LoggingMiddleware,
)
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging, LoggingMiddleware
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

- **Entities Management**: CRUD operations for mythological entities (characters, creatures, places, objects)
- **Countries**: Manage countries and their associated myths
- **Categories & Types**: Classify entities by category (Deity, Creature, Place) and mythological origin (Egyptian, Greek, Norse, etc.)
- **Relations**: Define relationships between entities (parent-child, siblings, enemies)
- **Characteristics**: Store powers, weaknesses, and physical features
- **Locations**: Geographic places associated with myths
- **Sources**: Reference original materials (books, manuscripts, oral traditions)
- **Authentication**: JWT-based authentication with OAuth2
- **User Management**: Role-based access control with superuser privileges
- **Rate Limiting**: Protection against brute force attacks
- **Security Headers**: Enhanced HTTP security headers

## Authentication

Use the `/api/v1/auth/login` endpoint to obtain an access token. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_token>
```

## Rate Limiting

- General endpoints: 60 requests per minute
- Authentication endpoints: 10 requests per minute
    """,
    version="1.0.0",
    openapi_url=f"/api/v{settings.API_VERSION}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Carlos Cativo",
        "email": "cativo23.kt@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Request ID (must be first to capture all requests)
app.add_middleware(RequestIDMiddleware)

# Structured logging (after RequestID to capture request_id)
app.add_middleware(LoggingMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Set all CORS enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        str(origin).replace("/", "") for origin in settings.BACKEND_CORS_ORIGINS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=f"/api/v{settings.API_VERSION}")

add_pagination(app)

add_exception_handler(app)

# Rate limiting (must be last to wrap all other middleware)
setup_rate_limiter(app)


@app.get("/")
def index():
    logger.info("Index endpoint called")
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "data": {
            "description": "This is the Myths and Legends API",
            "author": "Carlos Cativo <cativo23.kt@gmail.com>",
            "important-urls": [
                {"docs": f"{settings.SERVER_HOST}:{settings.APP_PORT}/docs"},
                {
                    "versions": {
                        "v1": f"{settings.SERVER_HOST}:{settings.APP_PORT}/api/v1"
                    }
                },
            ],
        },
    }

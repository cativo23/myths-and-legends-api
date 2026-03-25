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
    openapi_url=f"/api/v{settings.API_VERSION}/openapi.json",
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

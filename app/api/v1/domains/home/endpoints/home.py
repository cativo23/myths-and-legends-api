from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["home"])


@router.get(
    "/",
    summary="Home",
    description="Welcome endpoint with API information and documentation links.",
    responses={
        200: {"description": "API welcome message"},
    },
)
def index():
    """Return welcome message with API information."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} v1!",
        "data": {
            "current_version": "v1.0.0",
            "urls": [
                {
                    "openapi": f"{settings.SERVER_HOST}:{settings.APP_PORT}/api/v1/openapi.json"
                },
                {"docs": f"{settings.SERVER_HOST}:{settings.APP_PORT}/docs"},
                {"redoc": f"{settings.SERVER_HOST}:{settings.APP_PORT}/redoc"},
            ],
        },
    }

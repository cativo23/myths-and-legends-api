from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/")
def index():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} v1!",
        "data":
            {
                'current_version': "v1.0.0",
                "urls": [
                    {
                        "openapi": f"http://localhost:{settings.APP_PORT}/api/v1/openapi.json"
                    }
                ],
            }
    }

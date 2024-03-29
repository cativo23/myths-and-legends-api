from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

from typing import Union

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"/api/v{settings.API_VERSION}/openapi.json"
)

app.include_router(api_router, prefix=f"/api/v{settings.API_VERSION}")


@app.get("/")
def index():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "data":
            {
                "description": 'This is the Myths and Legends API',
                "author": 'Carlos Cativo <cativo23.kt@gmail.com>',
                "important-urls": [
                    {
                        "docs": f"{settings.SERVER_HOST}:{settings.APP_PORT}/docs"
                    },
                    {
                        "versions": {
                            "v1": f"{settings.SERVER_HOST}:{settings.APP_PORT}/api/v1"
                        }
                    }
                ],
            }
    }


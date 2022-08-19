from fastapi import APIRouter

from app.api.v1.endpoints import home, login, users#, utils

api_router = APIRouter()

api_router.include_router(home.router, tags=["home"])
api_router.include_router(login.router, tags=["login"])
#api_router.include_router(users.router, prefix="/users", tags=["users"])

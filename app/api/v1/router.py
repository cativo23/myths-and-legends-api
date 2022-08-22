from fastapi import APIRouter

from app.api.v1.endpoints import home, login, users, countries

api_router = APIRouter()

api_router.include_router(home.router, tags=["home"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(countries.router, prefix="/countries", tags=["countries"])
#api_router.include_router(users.router, prefix="/users", tags=["users"])

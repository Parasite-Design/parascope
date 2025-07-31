from fastapi import APIRouter

from .prospects import router as prospects_router
from .settings import router as settings_router
from .users import router as users_router

api_router = APIRouter()

api_router.include_router(users_router, tags=["authentication"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(prospects_router, prefix="/prospect", tags=["prospects"])

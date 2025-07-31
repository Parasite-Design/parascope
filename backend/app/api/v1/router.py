from fastapi import APIRouter

from .prospects import router as prospects_router
from .users import router as users_router

api_router = APIRouter()

api_router.include_router(users_router, tags=["authentification"])
api_router.include_router(prospects_router, prefix="/prospect", tags=["prospects"])

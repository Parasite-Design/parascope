from fastapi import APIRouter

from .customers import router as customers_router
from .dates import router as dates_router
from .models import router as models_router
from .products import router as products_router
from .prospects import router as prospects_router
from .representatives import router as representatives_router
from .settings import router as settings_router
from .statistics import router as statistics_router
from .users import router as users_router

api_router = APIRouter()

api_router.include_router(users_router, tags=["authentication"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(prospects_router, prefix="/prospect", tags=["prospects"])
api_router.include_router(statistics_router, prefix="/statistics", tags=["statistics"])
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(models_router, prefix="/models", tags=["models"])
api_router.include_router(customers_router, prefix="/customers", tags=["customers"])
api_router.include_router(dates_router, prefix="/dates", tags=["dates"])
api_router.include_router(
    representatives_router, prefix="/rep", tags=["representatives"]
)

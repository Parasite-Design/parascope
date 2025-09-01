from datetime import datetime
from typing import List, Optional

from app.core.database import get_db
from app.models.user import UserResponse
from app.services.models import get_models_service
from app.utils.security import get_current_user
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_models(
    start_date: datetime = Query(..., description="Filter prospects by brand"),
    end_date: datetime = Query(..., description="Filter prospects by brand"),
    brand: Optional[str] = None,
    include_no_sales: bool = False,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to get insights about models on a given period.
    """
    return await get_models_service(
        db, current_user, start_date, end_date, brand, include_no_sales
    )

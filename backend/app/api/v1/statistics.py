from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.user import UserResponse
from app.services.statistic import (
    get_customers_statistics_service,
    get_sales_statistics_service,
)
from app.utils.security import get_current_user
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.get("/sales", response_model=dict)
async def get_sales_statistics(
    brand: Optional[str] = Query(None),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to get insights about sales on a given period.
    """
    return await get_sales_statistics_service(
        db, current_user, start_date, end_date, brand
    )


@router.get("/customers", response_model=dict)
async def get_customers_statistics(
    brand: Optional[str] = Query(None),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to get insights about customers on a given period.
    """
    return await get_customers_statistics_service(
        db, current_user, start_date, end_date, brand
    )

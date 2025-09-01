from datetime import datetime
from typing import List

from app.core.database import get_db
from app.models.customers import CustomerUpdateRequest
from app.models.user import UserResponse
from app.services.customers import (
    get_customer_service,
    get_customers_service,
    update_customer_service,
)
from app.utils.security import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_customers(
    period1_start: datetime = Query(...),
    period1_end: datetime = Query(...),
    period2_start: datetime = Query(...),
    period2_end: datetime = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to get insights about customers on a given period.
    """
    return await get_customers_service(
        db, current_user, period1_start, period1_end, period2_start, period2_end
    )


@router.get("/{customer_id}", response_model=dict)
async def get_customer(
    customer_id: str,
    month_interval: int = Query(...),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to get insights about customers on a given period.
    """
    return await get_customer_service(
        db, current_user, period_start, period_end, customer_id, month_interval
    )


@router.put("/{customer_id}", response_model=dict)
async def update_customer(
    customer_id: str,
    update_data: CustomerUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update customer information.

    Allows updating of objective, visits count, favorite status, and notes
    for a specific customer. At least one field must be provided for update.
    """
    try:
        # Convert Pydantic model to dict and filter out None values
        update_dict = update_data.dict(exclude_unset=True)

        result = await update_customer_service(
            db=db, current_user=current_user, customer_id_str=customer_id, **update_dict
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail="Internal server error")

from typing import List

from app.core.database import get_db
from app.models.representatives import RepresentativeResponse
from app.models.user import UserResponse
from app.services.representatives import (
    get_representative_service,
    get_representatives_service,
)
from app.utils.security import admin_required, get_current_user
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.get("/", response_model=RepresentativeResponse)
async def get_representative(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    return await get_representative_service(current_user, db)


@router.get("/all", response_model=List[RepresentativeResponse])
async def get_representatives(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(admin_required),
):
    return await get_representatives_service(db)

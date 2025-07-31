from typing import List

from app.core.database import get_db
from app.models.settings import (
    BrandResponse,
    CreateBrandRequest,
    ObjectiveChangeRequest,
)
from app.models.user import UserResponse
from app.services.settings import (
    create_brand_service,
    delete_brand_service,
    get_all_brands_service,
    update_objective_service,
)
from app.utils.security import admin_required
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.post("/brand", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_brand(
    data: CreateBrandRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(admin_required),
):
    """
    Admin endpoint to add a brand to the whitelist.
    """
    result = await create_brand_service(data.brand_name, data.showed_brand_name, db)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to add brand to whitelist")
    return {"message": f"Brand '{data.brand_name}' added to whitelist."}


@router.get("/brand", response_model=List[BrandResponse])
async def get_all_brands(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Get a list of all brand names in the whitelist.
    """
    brands = await get_all_brands_service(db)
    return brands


@router.delete("/brand/{brand_name}", response_model=dict)
async def delete_brand(
    brand_name: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(admin_required),
):
    """
    Admin endpoint to delete a brand from the whitelist.
    """
    deleted = await delete_brand_service(brand_name, db)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Brand '{brand_name}' not found or could not be deleted",
        )
    return {"message": f"Brand '{brand_name}' deleted from whitelist."}


@router.post("/objective", response_model=dict, status_code=status.HTTP_200_OK)
async def update_objective(
    data: ObjectiveChangeRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(admin_required),
):
    """
    Admin endpoint to update a representative's objective value for a brand or all brands.
    """
    updated = await update_objective_service(
        rep_id=data.rep_id,
        brand_name=data.brand_name,
        objective_type=data.type,
        value=data.value,
        db=db,
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Representative not found or objective could not be updated",
        )
    return {"message": "Objective updated successfully."}

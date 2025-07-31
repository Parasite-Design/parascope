import csv
import io
from typing import List

from app.core.database import get_db
from app.models.prospect import ProspectCreate, ProspectResponse, ProspectUpdate
from app.models.user import UserResponse
from app.services.prospect import (
    create_prospect_service,
    delete_prospect_service,
    get_all_prospects_service,
    get_prospect_service,
    update_prospect_service,
)
from app.utils.security import get_current_user
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(
    prospect_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Retrieve a specific prospect by its ID.
    """
    return await get_prospect_service(prospect_id, db, current_user)


@router.post("/", response_model=ProspectResponse)
async def create_prospect(
    prospect: ProspectCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Create a new prospect.
    """
    return await create_prospect_service(prospect, db, current_user)


@router.put("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: str,
    prospect: ProspectUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update an existing prospect.
    """
    return await update_prospect_service(prospect_id, prospect, db, current_user)


@router.delete("/{prospect_id}", response_model=dict)
async def delete_prospect(
    prospect_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Delete a prospect by its ID.
    """
    await delete_prospect_service(prospect_id, db, current_user)
    return {"message": "Prospect deleted successfully"}


@router.get("/", response_model=List[ProspectResponse])
async def get_all_prospects(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Retrieve all prospects.
    """
    return await get_all_prospects_service(db, current_user)


@router.get("/export/csv", response_class=StreamingResponse)
async def export_prospects_csv(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Export all prospects as a CSV file.
    """
    prospects = await get_all_prospects_service(db, current_user)
    output = io.StringIO()
    writer = csv.writer(output)
    # Write header
    writer.writerow(
        [
            "id",
            "name",
            "contact_name",
            "status",
            "notes",
            "phone",
            "city",
            "address",
            "prospect_interest",
            "commercial_interest",
            "last_visit",
            "next_visit",
            "creator",
            "created_at",
            "updated_at",
        ]
    )
    # Write data rows
    for p in prospects:
        writer.writerow(
            [
                p.id,
                p.name,
                p.contact_name,
                p.status,
                p.notes,
                p.phone,
                p.city,
                p.address,
                p.prospect_interest,
                p.commercial_interest,
                p.last_visit,
                p.next_visit,
                p.creator,
                p.created_at,
                p.updated_at,
            ]
        )
    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=prospects.csv"}
    return StreamingResponse(output, media_type="text/csv", headers=headers)

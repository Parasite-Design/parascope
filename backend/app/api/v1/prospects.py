import csv
import io
import re
from enum import Enum
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.models.prospect import ProspectCreate, ProspectResponse, ProspectUpdate
from app.models.user import UserResponse
from app.services.prospect import (
    create_prospect_service,
    delete_prospect_service,
    get_all_prospects_service,
    get_prospect_service,
    mongo_to_prospect_response,
    update_prospect_service,
)
from app.utils.database import get_representative_code_by_mongo_id
from app.utils.geocoding import get_lat_long_osm
from app.utils.security import get_current_user
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

router = APIRouter()

VALID_SORT_FIELDS = [
    "name",
    "contact_name",
    "status",
    "email",
    "phone",
    "city",
    "country",
    "prospect_interest",
    "commercial_interest",
    "last_visit",
    "next_visit",
    "favorite",
    "created_at",
    "updated_at",
]


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


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ProspectFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    favorite: Optional[bool] = None
    brand: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[SortOrder] = SortOrder.DESC
    page: Optional[int] = 1
    limit: Optional[int] = 10


@router.get("/", response_model=Dict[str, Any])
async def get_all_prospects(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    favorite: Optional[str] = Query(None),  # Change to string first
    brand: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[SortOrder] = Query(SortOrder.DESC),
    page: Optional[int] = Query(1, ge=1),
    limit: Optional[int] = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get all prospects with filtering, sorting, and pagination.
    """
    # Build the filter query
    filter_query = {"representative_id": current_user.representative_id}

    if brand:
        filter_query["brands"] = brand

    if status:
        filter_query["status"] = status

    # Handle favorite filter properly
    if favorite is not None:
        # Convert string to boolean
        if favorite.lower() == "true":
            filter_query["favorite"] = True  # pyright: ignore[reportArgumentType]
        elif favorite.lower() == "false":
            filter_query["favorite"] = False  # pyright: ignore[reportArgumentType]
        # If it's anything else, we don't filter by favorite

    if search:
        # Create a regex pattern for case-insensitive search
        regex = re.compile(f".*{re.escape(search)}.*", re.IGNORECASE)
        filter_query["$or"] = [  # pyright: ignore[reportArgumentType]
            {"name": regex},
            {"contact_name": regex},
            {"email": regex},
            {"phone": regex},
            {"city": regex},
            {"country": regex},
            {"address": regex},
        ]

    # Validate sort field
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field. Must be one of: {', '.join(VALID_SORT_FIELDS)}",
        )

    # Determine sort order
    sort_direction = 1 if sort_order == SortOrder.ASC else -1

    # Calculate skip for pagination
    skip = (page - 1) * limit  # pyright: ignore[reportOperatorIssue, reportOptionalOperand]

    # Query MongoDB with filters, sorting, and pagination
    cursor = (
        db.prospects.find(filter_query)
        .sort(sort_by, sort_direction)
        .skip(skip)
        .limit(limit)  # pyright: ignore[reportArgumentType]
    )
    prospects = await cursor.to_list(length=limit)

    # Get total count for pagination
    total_count = await db.prospects.count_documents(filter_query)

    # Convert to response model
    response_prospects = [
        mongo_to_prospect_response(prospect) for prospect in prospects
    ]

    # Return response with pagination metadata
    return {
        "items": response_prospects,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "has_more": (page * limit) < total_count,  # pyright: ignore[reportOperatorIssue]
    }


@router.post("/{prospect_id}/locate", response_model=ProspectResponse)
async def locate_prospect(
    prospect_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Geolocate a prospect using its address, city, and country, and update its latitude and longitude.
    """
    # Fetch the prospect
    prospect = await get_prospect_service(prospect_id, db, current_user)
    try:
        latitude, longitude = get_lat_long_osm(
            prospect.country, prospect.city, prospect.address
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Prepare update data
    update_data = ProspectUpdate(
        latitude=latitude,
        longitude=longitude,
    )  # pyright: ignore[reportCallIssue]
    updated = await update_prospect_service(prospect_id, update_data, db, current_user)
    return updated


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
            "email",
            "city",
            "country",
            "address",
            "prospect_interest",
            "commercial_interest",
            "last_visit",
            "next_visit",
            "representative_id",
            "created_at",
            "updated_at",
            "latitude",
            "longitude",
            "brands",
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
                p.email,
                p.city,
                p.country,
                p.address,
                p.prospect_interest,
                p.commercial_interest,
                p.last_visit,
                p.next_visit,
                await get_representative_code_by_mongo_id(
                    ObjectId(p.representative_id), db
                ),
                p.created_at,
                p.updated_at,
                p.latitude,
                p.longitude,
                p.brands,
            ]
        )
    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=prospects.csv"}
    return StreamingResponse(output, media_type="text/csv", headers=headers)

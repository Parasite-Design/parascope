import datetime
from typing import List

from app.models.prospect import ProspectCreate, ProspectResponse, ProspectUpdate
from app.models.user import UserResponse
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase


def mongo_to_prospect_response(doc: dict) -> ProspectResponse:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return ProspectResponse(**doc)


def calculate_score(prospect_interest, commercial_interest):
    if prospect_interest is not None and commercial_interest is not None:
        return prospect_interest + commercial_interest
    return None


async def get_prospect_service(
    prospect_id: str, db: AsyncIOMotorDatabase, current_user: UserResponse
) -> ProspectResponse:
    try:
        obj_id = ObjectId(prospect_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid prospect ID")
    prospect = await db.prospects.find_one({"_id": obj_id})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    # Authorization: Only creator can access
    if prospect.get("rep_id") != current_user.rep_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this prospect"
        )
    return mongo_to_prospect_response(prospect)


async def create_prospect_service(
    prospect: ProspectCreate, db: AsyncIOMotorDatabase, current_user: UserResponse
) -> ProspectResponse:
    prospect_dict = prospect.model_dump()
    prospect_dict["rep_id"] = current_user.rep_id
    prospect_dict["created_at"] = datetime.datetime.now()
    prospect_dict["updated_at"] = datetime.datetime.now()
    score = calculate_score(
        prospect_dict.get("prospect_interest"),
        prospect_dict.get("commercial_interest"),
    )
    if score is not None:
        prospect_dict["score"] = score
    result = await db.prospects.insert_one(prospect_dict)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to create prospect")
    new_prospect = await db.prospects.find_one({"_id": result.inserted_id})
    return mongo_to_prospect_response(new_prospect)  # pyright: ignore[reportArgumentType]


async def update_prospect_service(
    prospect_id: str,
    prospect: ProspectUpdate,
    db: AsyncIOMotorDatabase,
    current_user: UserResponse,
) -> ProspectResponse:
    try:
        obj_id = ObjectId(prospect_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid prospect ID")
    existing = await db.prospects.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Prospect not found")
    if existing.get("rep_id") != current_user.rep_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this prospect"
        )
    update_data = prospect.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.datetime.now()
        await db.prospects.update_one({"_id": obj_id}, {"$set": update_data})
    updated_prospect = await db.prospects.find_one({"_id": obj_id})
    if not updated_prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return mongo_to_prospect_response(updated_prospect)


async def delete_prospect_service(
    prospect_id: str, db: AsyncIOMotorDatabase, current_user: UserResponse
) -> None:
    try:
        obj_id = ObjectId(prospect_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid prospect ID")
    existing = await db.prospects.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Prospect not found")
    if existing.get("rep_id") != current_user.rep_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this prospect"
        )
    result = await db.prospects.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prospect not found")


async def get_all_prospects_service(
    db: AsyncIOMotorDatabase, current_user: UserResponse
) -> List[ProspectResponse]:
    prospects_cursor = db.prospects.find({"rep_id": current_user.rep_id})
    prospects = []
    async for doc in prospects_cursor:
        prospects.append(mongo_to_prospect_response(doc))
    return prospects

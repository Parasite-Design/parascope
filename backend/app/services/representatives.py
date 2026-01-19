from typing import List

from app.models.representatives import RepresentativeResponse
from app.models.user import UserResponse
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase


def mongo_to_representative_response(doc: dict) -> RepresentativeResponse:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return RepresentativeResponse(**doc)


async def get_representative_service(
    current_user: UserResponse,
    db: AsyncIOMotorDatabase,
) -> RepresentativeResponse:
    try:
        obj_id = ObjectId(current_user.representative_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400, detail="This user is not associated to any representatives"
        )

    rep = await db.representatives.find_one({"_id": obj_id})

    if not rep:
        raise HTTPException(status_code=404, detail="Prospect not found")

    return mongo_to_representative_response(rep)


async def get_representatives_service(
    db: AsyncIOMotorDatabase,
) -> List[RepresentativeResponse]:
    representatives_cursor = db.representatives.find()
    representatives = []
    async for doc in representatives_cursor:
        representatives.append(mongo_to_representative_response(doc))
    return representatives

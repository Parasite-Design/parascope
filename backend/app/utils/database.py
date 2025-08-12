from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

async def get_representative_mongo_id(representative_id: int, db: AsyncIOMotorDatabase) -> Optional[ObjectId]:
    """
    Retrieve the MongoDB _id for a representative given their representative_id.

    Args:
        representative_id (int): The representative's integer ID.

    Returns:
        Optional[ObjectId]: The MongoDB _id if found, otherwise None.
    """
    representative = await db["representatives"].find_one({"code": representative_id})
    if representative:
        return representative.get("_id")
    return None

async def get_representative_code_by_mongo_id(mongo_id: ObjectId, db: AsyncIOMotorDatabase) -> Optional[int]:
    """
    Retrieve the representative's integer code given their MongoDB _id.

    Args:
        mongo_id (ObjectId): The MongoDB _id of the representative.

    Returns:
        Optional[int]: The representative's integer code if found, otherwise None.
    """
    representative = await db["representatives"].find_one({"_id": mongo_id})
    if representative:
        return representative.get("code")
    return None

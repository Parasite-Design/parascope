from typing import Optional

from app.define import ALL_BRAND_KEY
from app.models.settings import BrandResponse, ObjectiveTypeEnum
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError


async def create_brand_service(
    brand_name: str, showed_brand_name: str, db: AsyncIOMotorDatabase
) -> bool:
    """
    Inserts a new brand document into the 'brand' collection.

    Args:
        brand_name (str): The name of the brand to add.
        db (AsyncIOMotorDatabase): The database connection.

    Returns:
        bool: True if the brand was added successfully, False otherwise.
    """
    try:
        result = await db.brand.insert_one(
            {"brand_name": brand_name, "showed_brand_name": showed_brand_name}
        )
        return result.acknowledged
    except PyMongoError:
        return False


async def get_all_brands_service(db: AsyncIOMotorDatabase) -> list[BrandResponse]:
    """
    Retrieves all brand names from the 'brand' collection.

    Args:
        db (AsyncIOMotorDatabase): The database connection.

    Returns:
        list: List of brand.
    """
    try:
        brands_cursor = db.brand.find(
            {}, {"_id": 0, "brand_name": 1, "showed_brand_name": 1}
        )
        brands = [doc async for doc in brands_cursor]
        print(brands)
        return brands
    except PyMongoError as _:
        return []


async def delete_brand_service(brand_name: str, db: AsyncIOMotorDatabase) -> bool:
    """
    Deletes a brand document from the 'brand' collection by brand_name.

    Args:
        brand_name (str): The name of the brand to delete.
        db (AsyncIOMotorDatabase): The database connection.

    Returns:
        bool: True if a brand was deleted, False otherwise.
    """
    try:
        result = await db.brand.delete_one({"brand_name": brand_name})
        return result.deleted_count > 0
    except PyMongoError:
        return False


async def update_objective_service(
    rep_id: str,
    brand_name: Optional[str],
    objective_type: ObjectiveTypeEnum,
    value: int,
    db: AsyncIOMotorDatabase,
) -> bool:
    """
    Updates the objective value for a representative, for a specific brand or all brands.

    Args:
        rep_id (str): Representative ID.
        brand_name (Optional[str]): Brand name or None for all brands.
        objective_type (ObjectiveTypeEnum): The type of objective to update.
        value (int): The value to set.
        db (AsyncIOMotorDatabase): The database connection.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    try:
        if not ObjectId.is_valid(rep_id):
            return False
        if brand_name is not None and not isinstance(brand_name, str):
            return False
        if not isinstance(objective_type, ObjectiveTypeEnum):
            return False
        if not isinstance(value, int):
            return False

        brand_key = brand_name if brand_name else ALL_BRAND_KEY
        update_path = f"objectives.{brand_key}.{objective_type.value}"
        result = await db.representatives.update_one(
            {"_id": ObjectId(rep_id)},
            {"$set": {update_path: value}},
        )
        return result.modified_count > 0
    except PyMongoError:
        return False

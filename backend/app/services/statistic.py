from app.models.user import UserResponse
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

async def get_sales_statistics_service(
    db: AsyncIOMotorDatabase, current_user: UserResponse, start_date: datetime, end_date: datetime
) -> dict:
    if not current_user.representative_id:
        raise ValueError("Missing representative_id for current user.")

    pipeline = [
        {"$match": {
            "order_date": {"$gte": start_date, "$lte": end_date},
            "representative_id": ObjectId(current_user.representative_id)
        }},
        {"$group": {
            "_id": None,
            "sales": {"$sum": "$total"},
            "units": {"$sum": "$quantity"},
            "web_sales": {"$sum": {"$cond": [{"$regexMatch": {"input": "$code", "regex": "^W"}}, "$total", 0]}},
            "direct_sales": {"$sum": {"$cond": [{"$eq": ["$type", "direct"]}, "$total", 0]}},
            "return": {"$sum": {"$cond": [{"$eq": ["$type", "return"]}, "$total", 0]}}
        }}
    ]
    result = await db.invoices.aggregate(pipeline).to_list(1)
    statistics = result[0] if result else {
        "sales": 0.0,
        "units": 0,
        "web_sales": 0.0,
        "direct_sales": 0.0,
        "return": 0.0
    }
    statistics["average_price"] = statistics["sales"] / statistics["units"] if statistics["units"] else 0.0

    if "_id" in statistics:
        del statistics["_id"]  # Remove the _id field if present

    return statistics

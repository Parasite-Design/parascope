from datetime import datetime
from typing import Optional

from app.models.user import UserResponse
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_sales_statistics_service(
    db: AsyncIOMotorDatabase,
    current_user: UserResponse,
    start_date: datetime,
    end_date: datetime,
    brand: Optional[str] = None,  # Added optional brand parameter
) -> dict:
    if not current_user.representative_id:
        raise ValueError("Missing representative_id for current user.")

    # Build the base match condition
    match_condition = {
        "order_date": {"$gte": start_date, "$lte": end_date},
        "representative_id": ObjectId(current_user.representative_id),
    }

    # Add brand filter if provided
    if brand:
        match_condition["brand"] = brand

    pipeline = [
        {"$match": match_condition},
        {
            "$group": {
                "_id": None,
                "sales": {"$sum": "$total"},
                "units": {"$sum": "$quantity"},
                "web_sales": {
                    "$sum": {
                        "$cond": [
                            {"$regexMatch": {"input": "$code", "regex": "^W"}},
                            "$total",
                            0,
                        ]
                    }
                },
                "direct_sales": {
                    "$sum": {"$cond": [{"$eq": ["$type", "direct"]}, "$total", 0]}
                },
                "return": {
                    "$sum": {"$cond": [{"$eq": ["$type", "return"]}, "$total", 0]}
                },
            }
        },
    ]

    result = await db.invoices.aggregate(pipeline).to_list(1)
    statistics = (
        result[0]
        if result
        else {
            "sales": 0.0,
            "units": 0,
            "web_sales": 0.0,
            "direct_sales": 0.0,
            "return": 0.0,
        }
    )
    statistics["average_price"] = (
        statistics["sales"] / statistics["units"] if statistics["units"] else 0.0
    )

    if "_id" in statistics:
        del statistics["_id"]

    return statistics


async def get_customers_statistics_service(
    db: AsyncIOMotorDatabase,
    current_user: UserResponse,
    start_date: datetime,
    end_date: datetime,
    brand: Optional[str] = None,  # Added optional brand parameter
) -> dict:
    if not current_user.representative_id:
        raise ValueError("Missing representative_id for current user.")

    # Build the base invoice match condition for the lookup
    invoice_match_condition = {
        "$expr": {
            "$and": [
                {"$eq": ["$customer_id", "$$customerId"]},
                {"$gte": ["$invoice_date", start_date]},
                {"$lte": ["$invoice_date", end_date]},
            ]
        }
    }

    # Add brand filter if provided
    if brand:
        invoice_match_condition["$expr"]["$and"].append({"$eq": ["$brand", brand]})

    pipeline = [
        {"$match": {"representative_id": ObjectId(current_user.representative_id)}},
        {
            "$lookup": {
                "from": "invoices",
                "let": {"customerId": "$_id"},
                "pipeline": [{"$match": invoice_match_condition}],
                "as": "invoices",
            }
        },
        {"$addFields": {"invoice_count": {"$size": "$invoices"}}},
        {
            "$group": {
                "_id": None,
                "customers": {
                    "$sum": {
                        "$cond": {
                            "if": {"$gte": ["$invoice_count", 1]},
                            "then": 1,
                            "else": 0,
                        }
                    }
                },
                "active_customers": {
                    "$sum": {
                        "$cond": {
                            "if": {"$gte": ["$invoice_count", 4]},
                            "then": 1,
                            "else": 0,
                        }
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "customers": 1,
                "active_customers": 1,
            }
        },
    ]

    result = await db.customers.aggregate(pipeline).to_list(1)
    statistics = result[0] if result else {"customers": 0, "active_customers": 0}

    if "_id" in statistics:
        del statistics["_id"]

    return statistics

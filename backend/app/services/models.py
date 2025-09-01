from datetime import datetime
from typing import List, Optional

from app.models.user import UserResponse
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_models_service(
    db: AsyncIOMotorDatabase,
    current_user: UserResponse,
    start_date: datetime,
    end_date: datetime,
    brand: Optional[str] = None,
    include_no_sales=False,
) -> List[dict]:
    if not current_user.representative_id:
        raise ValueError("Missing representative_id for current user.")

    pipeline = [
        {
            "$lookup": {
                "from": "brand",
                "localField": "brand",
                "foreignField": "brand_name",
                "as": "brand_match",
            }
        },
        {"$match": {"brand_match": {"$not": {"$size": 0}}}},
        {"$unset": "brand_match"},
    ]

    if brand:
        pipeline.append({"$match": {"brand": brand}})

    pipeline.append(
        {
            "$lookup": {
                "from": "invoices",
                "let": {"modelID": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$model_id", "$$modelID"]},
                                    {"$gte": ["$invoice_date", start_date]},
                                    {"$lte": ["$invoice_date", end_date]},
                                ]
                            }
                        }
                    }
                ],
                "as": "invoices",
            }
        },
    )

    if not include_no_sales:
        pipeline.append({"$match": {"invoices": {"$not": {"$size": 0}}}})

    pipeline += [
        {"$addFields": {"sales": {"$sum": "$invoices.quantity"}}},
        {"$addFields": {"total": {"$sum": "$invoices.total"}}},
        {
            "$addFields": {
                "web_sales": {
                    "$reduce": {
                        "input": "$invoices",
                        "initialValue": 0,
                        "in": {
                            "$add": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$regexMatch": {
                                                "input": "$$this.code",
                                                "regex": "^W",
                                            }
                                        },
                                        "$$this.quantity",
                                        0,
                                    ]
                                },
                            ]
                        },
                    }
                }
            }
        },
        {
            "$addFields": {
                "web_total": {
                    "$reduce": {
                        "input": "$invoices",
                        "initialValue": 0,
                        "in": {
                            "$add": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$regexMatch": {
                                                "input": "$$this.code",
                                                "regex": "^W",
                                            }
                                        },
                                        "$$this.total",
                                        0,
                                    ]
                                },
                            ]
                        },
                    }
                }
            }
        },
        {
            "$addFields": {
                "invoices": {
                    "$filter": {
                        "input": "$invoices",
                        "as": "inv",
                        "cond": {
                            "$eq": [
                                "$$inv.representative_id",
                                ObjectId("689372fe54b73e426d99b382"),
                            ]
                        },
                    }
                }
            }
        },
        {"$addFields": {"my_sales": {"$sum": "$invoices.quantity"}}},
        {"$addFields": {"my_total": {"$sum": "$invoices.total"}}},
        {
            "$addFields": {
                "my_web_sales": {
                    "$reduce": {
                        "input": "$invoices",
                        "initialValue": 0,
                        "in": {
                            "$add": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$regexMatch": {
                                                "input": "$$this.code",
                                                "regex": "^W",
                                            }
                                        },
                                        "$$this.quantity",
                                        0,
                                    ]
                                },
                            ]
                        },
                    }
                }
            }
        },
        {
            "$addFields": {
                "my_web_total": {
                    "$reduce": {
                        "input": "$invoices",
                        "initialValue": 0,
                        "in": {
                            "$add": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$regexMatch": {
                                                "input": "$$this.code",
                                                "regex": "^W",
                                            }
                                        },
                                        "$$this.total",
                                        0,
                                    ]
                                },
                            ]
                        },
                    }
                }
            }
        },
        {
            "$addFields": {
                "edi": {
                    "$reduce": {
                        "input": "$invoices",
                        "initialValue": 0,
                        "in": {
                            "$add": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$regexMatch": {
                                                "input": "$$this.code",
                                                "regex": "^Z",
                                            }
                                        },
                                        "$$this.total",
                                        0,
                                    ]
                                },
                            ]
                        },
                    }
                }
            }
        },
        {"$unset": "invoices"},
        {"$unset": "_id"},
        {"$unset": "product_id"},
    ]

    result = await db.models.aggregate(pipeline).to_list()

    return result

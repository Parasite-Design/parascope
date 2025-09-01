from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from dateutil.relativedelta import relativedelta
from motor.motor_asyncio import AsyncIOMotorDatabase


def compute_visits_and_last(
    cust: dict,
    compute_count: bool = False,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> None:
    invoices = cust.get("invoices", [])
    grouped = defaultdict(lambda: {"qty": 0, "total": 0, "last_date": None})

    for inv in invoices:
        code = inv.get("code")
        qty = inv.get("quantity", 0) or 0
        total = inv.get("total", 0) or 0
        date = inv.get("order_date")

        if not code:
            continue
        grouped[code]["qty"] += qty  # pyright: ignore[reportOperatorIssue]
        grouped[code]["total"] += total  # pyright: ignore[reportOperatorIssue]
        if grouped[code]["last_date"] is None or (
            date and date > grouped[code]["last_date"]
        ):
            grouped[code]["last_date"] = date

    visits = []
    for code, info in grouped.items():
        if code.startswith("A") and info["qty"] >= 10:  # pyright: ignore[reportOptionalOperand]
            visits.append(
                {
                    "code": code,
                    "date": info["last_date"],
                    "quantity": info["qty"],
                    "total": info["total"],
                }
            )

    cust["visits"] = visits
    cust["last_visit"] = max((v["date"] for v in visits), default=None)

    if cust.get("visits_count") is None and compute_count:
        cust["visits_count"] = 2


async def get_customers_service(
    db: AsyncIOMotorDatabase,
    current_user,
    period1_start: datetime,
    period1_end: datetime,
    period2_start: datetime,
    period2_end: datetime,
) -> List[dict]:
    if not current_user.representative_id:
        raise ValueError("Missing representative_id for current user.")

    pipeline = [
        # Only customers for this representative
        {"$match": {"representative_id": ObjectId(current_user.representative_id)}},
        # Lookup all invoices for this customer
        {
            "$lookup": {
                "from": "invoices",
                "localField": "_id",
                "foreignField": "customer_id",
                "as": "invoices",
            }
        },
        # Period 1 / Period 2 totals & counts (order_date based)
        {
            "$addFields": {
                "period1_total": {
                    "$sum": {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$invoices",
                                    "as": "inv",
                                    "cond": {
                                        "$and": [
                                            {
                                                "$gte": [
                                                    "$$inv.order_date",
                                                    period1_start,
                                                ]
                                            },
                                            {"$lte": ["$$inv.order_date", period1_end]},
                                        ]
                                    },
                                }
                            },
                            "as": "p1",
                            "in": "$$p1.total",
                        }
                    }
                },
                "period1_count": {
                    "$size": {
                        "$filter": {
                            "input": "$invoices",
                            "as": "inv",
                            "cond": {
                                "$and": [
                                    {"$gte": ["$$inv.order_date", period1_start]},
                                    {"$lte": ["$$inv.order_date", period1_end]},
                                ]
                            },
                        }
                    }
                },
                "period2_total": {
                    "$sum": {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$invoices",
                                    "as": "inv",
                                    "cond": {
                                        "$and": [
                                            {
                                                "$gte": [
                                                    "$$inv.order_date",
                                                    period2_start,
                                                ]
                                            },
                                            {"$lte": ["$$inv.order_date", period2_end]},
                                        ]
                                    },
                                }
                            },
                            "as": "p2",
                            "in": "$$p2.total",
                        }
                    }
                },
            }
        },
        # Objective and visits_count placeholders
        {
            "$addFields": {
                "objective": {
                    "$cond": [
                        {"$ifNull": ["$objective", False]},
                        "$objective",
                        "$period2_total",
                    ]
                },
                "visits_count": {
                    "$cond": [
                        {"$ifNull": ["$visits_count", False]},
                        "$visits_count",
                        None,  # we'll fill it in Python
                    ]
                },
                "favorite": {"$ifNull": ["$favorite", False]},
                "active": {"$gte": ["$period1_count", 4]},
            }
        },
        {
            "$project": {
                "_id": 1,
                "code": 1,
                "name": 1,
                "city": 1,
                "phone": 1,
                "latitude": 1,
                "longitude": 1,
                "period1_total": 1,
                "period1_count": 1,
                "period2_total": 1,
                "objective": 1,
                "visits_count": 1,
                "favorite": 1,
                "active": 1,
                "invoices.code": 1,
                "invoices.quantity": 1,
                "invoices.total": 1,
                "invoices.order_date": 1,
            }
        },
    ]

    customers = await db.customers.aggregate(pipeline).to_list(None)

    # --- Post-process visits in Python ---
    for cust in customers:
        compute_visits_and_last(
            cust, compute_count=True, period_start=period1_start, period_end=period1_end
        )
        cust["_id"] = str(cust["_id"])
        # Cleanup
        del cust["invoices"]
        del cust["visits"]

    return customers


async def get_customer_service(
    db: AsyncIOMotorDatabase,
    current_user,
    period_start: datetime,
    period_end: datetime,
    customer_id_str: str,
    month_interval: int,
) -> dict:
    if not current_user.representative_id:
        raise ValueError("Missing representative_id for current user.")

    customer_id = ObjectId(customer_id_str)

    pipeline = [
        # Only this customer for this representative
        {
            "$match": {
                "_id": customer_id,
                "representative_id": ObjectId(current_user.representative_id),
            }
        },
        # Lookup all invoices for this customer
        {
            "$lookup": {
                "from": "invoices",
                "localField": "_id",
                "foreignField": "customer_id",
                "as": "invoices",
            }
        },
        # Project only necessary fields for invoices to avoid ObjectIds
        {
            "$addFields": {
                "invoices": {
                    "$map": {
                        "input": "$invoices",
                        "as": "inv",
                        "in": {
                            "code": "$$inv.code",
                            "quantity": "$$inv.quantity",
                            "total": "$$inv.total",
                            "order_date": "$$inv.order_date",
                        },
                    }
                }
            }
        },
        # Add period totals & counts (order_date based)
        {
            "$addFields": {
                "period1_total": {
                    "$sum": {
                        "$map": {
                            "input": {
                                "$filter": {
                                    "input": "$invoices",
                                    "as": "inv",
                                    "cond": {
                                        "$and": [
                                            {
                                                "$gte": [
                                                    "$$inv.order_date",
                                                    period_start,
                                                ]
                                            },
                                            {"$lte": ["$$inv.order_date", period_end]},
                                        ]
                                    },
                                }
                            },
                            "as": "p1",
                            "in": "$$p1.total",
                        }
                    }
                },
                "period1_count": {
                    "$size": {
                        "$filter": {
                            "input": "$invoices",
                            "as": "inv",
                            "cond": {
                                "$and": [
                                    {"$gte": ["$$inv.order_date", period_start]},
                                    {"$lte": ["$$inv.order_date", period_end]},
                                ]
                            },
                        }
                    }
                },
            }
        },
        # Objective and other fields
        {
            "$addFields": {
                "objective": {
                    "$cond": [
                        {"$ifNull": ["$objective", False]},
                        "$objective",
                        0,
                    ]
                },
                "visits_count": {
                    "$cond": [
                        {"$ifNull": ["$visits_count", False]},
                        "$visits_count",
                        None,  # we'll fill it in Python
                    ]
                },
                "favorite": {"$ifNull": ["$favorite", False]},
                "note": {"$ifNull": ["$note", ""]},
            }
        },
        # Project final fields
        {
            "$project": {
                "_id": 0,
                "code": 1,
                "name": 1,
                "city": 1,
                "phone": 1,
                "latitude": 1,
                "longitude": 1,
                "period1_total": 1,
                "period1_count": 1,
                "objective": 1,
                "visits_count": 1,
                "favorite": 1,
                "note": 1,
                "invoices.code": 1,
                "invoices.quantity": 1,
                "invoices.total": 1,
                "invoices.order_date": 1,
            }
        },
    ]

    customers = await db.customers.aggregate(pipeline).to_list(None)

    if not customers:
        raise ValueError("Customer not found or not authorized.")

    customer = customers[0]

    # --- Post-process visits in Python ---
    compute_visits_and_last(customer)

    # --- Compute period sums in Python ---
    now = datetime.now()
    six_years_ago = now - relativedelta(years=6)
    periods = []
    end = now
    while end > six_years_ago:
        start = end - relativedelta(months=month_interval)
        if start < six_years_ago:
            start = six_years_ago
        periods.append({"start": start, "end": end})
        end = start

    # periods is from most recent to oldest
    period_sums = []
    for p in periods:
        invs_in_p = [
            inv
            for inv in customer["invoices"]
            if inv.get("order_date") and p["start"] <= inv["order_date"] < p["end"]
        ]
        total = sum(inv.get("total", 0) for inv in invs_in_p)
        count = len(invs_in_p)
        period_sums.append(
            {"start": p["start"], "end": p["end"], "total": total, "count": count}
        )

    customer["period_sums"] = period_sums

    del customer["invoices"]

    return customer


async def update_customer_service(
    db: AsyncIOMotorDatabase,
    current_user,
    customer_id_str: str,
    objective: Optional[int] = None,
    visits_count: Optional[int] = None,
    favorite: Optional[bool] = None,
    note: Optional[str] = None,
) -> dict:
    if not current_user.representative_id:
        raise ValueError("Missing representative_id for current user.")

    customer_id = ObjectId(customer_id_str)
    rep_id = ObjectId(current_user.representative_id)

    set_dict = {}
    if objective is not None:
        set_dict["objective"] = objective
    if visits_count is not None:
        set_dict["visits_count"] = visits_count
    if favorite is not None:
        set_dict["favorite"] = favorite
    if note is not None:
        set_dict["note"] = note

    if not set_dict:
        raise ValueError("No fields provided to update.")

    result = await db.customers.update_one(
        {"_id": customer_id, "representative_id": rep_id}, {"$set": set_dict}
    )

    if result.modified_count == 0:
        raise ValueError("Customer not found, not authorized, or no changes made.")

    return {"success": True, "updated_fields": list(set_dict.keys())}

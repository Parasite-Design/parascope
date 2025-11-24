import math
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from dateutil.relativedelta import relativedelta
from motor.motor_asyncio import AsyncIOMotorDatabase


def compute_visits_and_last(cust: dict) -> None:
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

    # Safely get last_visit - handle empty visits list
    if visits:
        cust["last_visit"] = max(
            (v["date"] for v in visits if v["date"] is not None), default=None
        )
    else:
        cust["last_visit"] = None

    # Calculate next_visit - handle None last_visit
    last_visit = cust.get("last_visit")
    visits_count = cust.get("visits_count", 2)  # Default to 2 if not set

    if last_visit and visits_count and visits_count > 0:
        try:
            # Calculate months between visits (12 months / visits_count)
            months_between = 12 / visits_count
            next_visit = last_visit + relativedelta(months=math.ceil(months_between))
            cust["next_visit"] = next_visit
        except (TypeError, ValueError) as e:
            print(f"Error calculating next_visit for customer {cust.get('code')}: {e}")
            cust["next_visit"] = None
    else:
        # If no last_visit, set next_visit to None or you could set a default
        cust["next_visit"] = None

    # Ensure visits_count has a default value
    if cust.get("visits_count") is None:
        cust["visits_count"] = 2


def score_client(client: dict) -> float:
    """
    Calculate a priority score for the client.
    Higher score means higher priority to contact.
    """
    # Use period2_total as last year's total (ly_total)
    ly_total = client.get("period2_total", 0)
    client_score = float(ly_total)

    if client_score == 0:
        # If no sales history, set a base score for new customers
        client_score = 100

    # Calculate year-over-year difference percentage
    period1_total = client.get("period1_total", 0)
    period2_total = client.get("period2_total", 0)

    if period2_total > 0:
        ly_diff = ((period1_total - period2_total) / period2_total) * 100
    else:
        ly_diff = 100 if period1_total > 0 else 0  # New customer or no sales

    # Apply LY difference factor - inverted so negative growth increases priority
    # If sales are down (negative ly_diff), we want higher priority
    ly_diff_factor = (100 + min(max(ly_diff, -99), 99)) / 10
    client_score *= ly_diff_factor

    # Apply time since last visit factor
    now = datetime.now()
    last_visit = client.get("last_visit")
    if last_visit and isinstance(last_visit, datetime):
        days_since_visit = (now - last_visit).days
        # Convert to 6-month periods, with minimum of 4
        six_month_periods = max(days_since_visit / (30.5 * 6), 4)
        client_score *= six_month_periods
    else:
        # No last visit - treat as very old visit to increase priority
        client_score *= 20  # Equivalent to ~3 years without visit

    # Apply objective difference factor
    objective = client.get("objective", 0)
    if objective > 0:
        objective_diff = ((objective - period1_total) / objective) * 100
        # Inverted: if below objective, increase priority
        objective_factor = (100 + min(max(objective_diff, -99), 99)) / 10
        client_score *= objective_factor

    client["score"] = round(client_score, 2)
    return client_score


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
                        2,  # Default to 2 if not set
                    ]
                },
                "favorite": {"$ifNull": ["$favorite", False]},
                "active": {"$gte": ["$period1_count", 4]},
            }
        },
        # Add computed fields: period_progress & objective_progress
        {
            "$addFields": {
                "period_progress": {
                    "$cond": [
                        {"$gt": ["$period2_total", 0]},
                        {
                            "$multiply": [
                                {"$divide": ["$period1_total", "$period2_total"]},
                                100,
                            ]
                        },
                        0,
                    ]
                },
                "objective_progress": {
                    "$cond": [
                        {"$gt": ["$objective", 0]},
                        {
                            "$multiply": [
                                {"$divide": ["$period1_count", "$objective"]},
                                100,
                            ]
                        },
                        0,
                    ]
                },
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
                "period_progress": 1,
                "objective_progress": 1,
                "invoices.code": 1,
                "invoices.quantity": 1,
                "invoices.total": 1,
                "invoices.order_date": 1,
            }
        },
    ]

    customers = await db.customers.aggregate(pipeline).to_list(None)

    # --- Post-process visits and scores in Python ---
    for cust in customers:
        compute_visits_and_last(cust)
        score_client(cust)  # Calculate priority score
        cust["_id"] = str(cust["_id"])
        # Cleanup
        del cust["invoices"]
        # Note: We keep "visits" for the detailed view

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

    # Calculate period2 (last year) for scoring
    period2_start = period_start - relativedelta(years=1)
    period2_end = period_end - relativedelta(years=1)

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
        # Add period totals & counts for both current and previous year
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
                        2,  # Default to 2 if not set
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
                "period2_total": 1,
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

    # --- Post-process visits and scores in Python ---
    compute_visits_and_last(customer)
    score_client(customer)  # Calculate priority score

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

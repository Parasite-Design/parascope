from datetime import date, datetime

from app.models.user import UserResponse
from app.utils.security import get_current_user
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.get("/n/{n}", response_model=dict)
async def get_sale_year(
    n: int,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to get a given sales period.

    n should be a value between 0 and -6

    n = 0: current sale period
    n = -1: last sale period
    etc...
    """

    if n > 0 or n < -5:
        # since currently no invoices in the database are older than 6 year n is caped at -5
        # if this isn't the case anymore you can change this code to allow for older dates
        raise HTTPException(
            status_code=406, detail="n should be a value between 0 and -5"
        )

    if date.today() > date(datetime.today().year, 9, 1):
        n += 1

    next_period_start = date(datetime.today().year + n, 9, 1)

    return {
        "period_start": next_period_start - relativedelta(years=1),
        "period_end": next_period_start - relativedelta(days=1),
    }


@router.get("/rolling-year", response_model=dict)
async def get_rolling_year(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to get a period corresponding to the current rolling year.
    """
    return {
        "period_start": date.today() - relativedelta(years=1),
        "period_end": date.today(),
    }

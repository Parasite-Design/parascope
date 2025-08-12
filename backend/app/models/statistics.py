from datetime import datetime

from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    start_date: datetime = Field(
        ...,
        description="Start date of the statistics data",
    )
    end_date: datetime = Field(
        ...,
        description="Start date of the statistics data",
    )

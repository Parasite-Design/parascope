from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# Pydantic model for customer update request
class CustomerUpdateRequest(BaseModel):
    objective: Optional[float] = Field(
        None,
        description="The customer's objective value",
        ge=0,  # Ensures value is greater than or equal to 0 if provided
    )
    visits_count: Optional[int] = Field(
        None,
        description="The number of visits to the customer",
        ge=0,  # Ensures value is greater than or equal to 0 if provided
    )
    favorite: Optional[bool] = Field(
        None, description="Whether this customer is marked as a favorite"
    )
    note: Optional[str] = Field(
        None,
        description="Additional notes about the customer",
        max_length=500,  # Limits note length
    )

    class Config:
        json_schema_extra = {
            "example": {
                "objective": 100,
                "visits_count": 5,
                "favorite": True,
                "note": "Important client with specific needs",
            }
        }

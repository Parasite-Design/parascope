from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ObjectiveTypeEnum(str, Enum):
    SALES_PER_CUSTOMER = "salesPerCustomer"
    ACTIVE_CUSTOMER = "activeCustomers"


class BrandBase(BaseModel):
    brand_name: str = Field(
        ...,
        description="Name of the brand to add to the database (value in the sage database)",
    )
    showed_brand_name: str = Field(
        ...,
        description="Name of the brand to add to the database (official brand name)",
    )


class CreateBrandRequest(BrandBase):
    pass


class BrandResponse(BrandBase):
    pass

class ObjectiveChangeRequest(BaseModel):
    rep_id: str = Field(..., description="Rep ID of the representative")
    brand_name: Optional[str] = Field(
        None,
        description="Name of the brand where the objective should be set, let empty for all brand",
    )  # pyright: ignore[reportAssignmentType]
    type: ObjectiveTypeEnum = Field(
        ..., description="Objective to set for the representative"
    )
    value: int = Field(..., description="Value of the objective to set")

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    NEW = "New"
    PENDING = "Pending"
    LOST = "Lost"
    CONVERTED = "Converted"
    READY = "Ready"
    BLOCKED = "Blocked"


class RepresentativeBase(BaseModel):
    id: str = Field(..., description="The id of the representative")
    code: int = Field(..., description="The code associated to this representative")
    key: str = Field(
        ...,
        description="Small key used to refer to a representative, most often just a contraction of the name",
    )
    name: str = Field(..., description="Name of the representative")
    objectives: Optional[dict] = Field(
        {}, description="Potential objectives associated to the representatives"
    )


class RepresentativeResponse(RepresentativeBase):
    """
    Model for returning a representative (e.g., from DB).
    """

    pass

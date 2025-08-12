from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """
    Shared properties for user models (excluding sensitive fields).
    """

    id: str
    email: str
    is_admin: bool = False
    representative_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    """
    Properties required to create a new user.
    """

    email: EmailStr = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    is_admin: bool = False
    representative_id: Optional[int] = None

    @field_validator("password")
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Add more checks as needed (e.g., numbers, special chars)
        return v


class UserLogin(BaseModel):
    """
    Properties required for user login.
    """

    email: EmailStr = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class UserModify(BaseModel):
    """
    Properties that can be modified for a user.
    """

    email: Optional[EmailStr] = Field(None, min_length=5, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_admin: Optional[bool] = None
    representative_id: Optional[int] = None


class UserResponse(UserBase):
    """
    User data returned in API responses (no password).
    """

    id: str
    email: str
    is_admin: bool = False
    representative_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserToken(BaseModel):
    """
    Token response containing authentication tokens and user info.
    """

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class LoginRequest(BaseModel):
    """
    Properties required for user login.
    """

    email: Optional[EmailStr] = Field(None, min_length=5, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminResetPasswordRequest(BaseModel):
    user_id: str = Field(..., description="Target user's ID")
    new_password: str = Field(..., min_length=8, max_length=128)

from datetime import datetime, timedelta
from typing import Optional

import jwt
from app.core.config import settings
from app.core.database import get_db
from app.models.user import UserResponse
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # Changed import
from jwt import PyJWTError
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

# Replaced OAuth2PasswordBearer with HTTPBearer
bearer_scheme = HTTPBearer(auto_error=False)  # Changed security scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,  # pyright: ignore[reportArgumentType]
        algorithm=settings.JWT_ALGORITHM,  # pyright: ignore[reportArgumentType]
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,  # pyright: ignore[reportArgumentType]
            algorithms=[settings.JWT_ALGORITHM],  # pyright: ignore[reportArgumentType]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        try:
            user_object_id = ObjectId(user_id)
        except (InvalidId, TypeError):
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user = await db.users.find_one({"_id": user_object_id})
    if user is None:
        raise credentials_exception

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        is_admin=user.get("is_admin", False),
        representative_id=str(user.get("representative_id")),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
    )


async def admin_required(current_user: UserResponse = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user

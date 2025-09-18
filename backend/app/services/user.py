import secrets
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
from app.core.config import settings
from app.models.user import UserCreate, UserResponse, UserToken
from app.utils.database import get_representative_mongo_id
from app.utils.security import create_access_token, hash_password, verify_password
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from jwt import PyJWTError
from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_user_service(user: UserCreate, db: AsyncIOMotorDatabase) -> UserToken:
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user and secrets.compare_digest(existing_user["email"], user.email):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(user.password)

    # Convert representative_id (int) to ObjectId if provided
    representative_object_id: Optional[ObjectId] = None
    if user.representative_id is not None:
        representative_object_id = await get_representative_mongo_id(
            user.representative_id, db
        )
        if representative_object_id is None:
            raise HTTPException(status_code=404, detail="Representative not found")

    # Prepare user document
    now = datetime.now()
    user_doc = {
        "email": user.email,
        "password": hashed_password,
        "is_admin": user.is_admin,
        "representative_id": representative_object_id,  # Store ObjectId or None
        "created_at": now,
        "updated_at": now,
    }

    # Insert user into DB
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Generate tokens
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # Store refresh token in DB for revocation support
    await db.users.update_one(
        {"_id": result.inserted_id}, {"$set": {"refresh_token": refresh_token}}
    )

    # Prepare user response (excluding password)
    user_response = UserResponse(
        id=user_id,
        email=user.email,
        is_admin=user.is_admin,
        representative_id=str(
            representative_object_id
        ),  # Still return the int code in response
        created_at=now,
        updated_at=now,
    )

    return UserToken(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
    )


async def login_user_service(
    email: str, password: str, db: AsyncIOMotorDatabase
) -> UserToken:
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    now = datetime.now()

    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # Update refresh token in DB
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"refresh_token": refresh_token, "updated_at": now}},
    )

    user_response = UserResponse(
        id=user_id,
        email=user["email"],
        is_admin=user.get("is_admin", False),
        representative_id=str(user.get("representative_id")),
        created_at=user.get("created_at"),
        updated_at=now,
    )

    return UserToken(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
    )


async def logout_user_service(user_id: ObjectId, db):
    """
    Invalidate the user's refresh token (logout).
    """
    result = await db.users.update_one(
        {"_id": user_id},
        {"$set": {"refresh_token": None}},
    )
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"message": "Logged out successfully"}


async def refresh_token_service(
    refresh_token: str, db: AsyncIOMotorDatabase
) -> UserToken:
    """
    Service to refresh access token using a valid refresh token.
    """
    try:
        # Verify the refresh token
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,  # pyright: ignore[reportArgumentType]
            algorithms=[settings.JWT_ALGORITHM],  # pyright: ignore[reportArgumentType]
        )

        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Convert to ObjectId
        try:
            user_oid = ObjectId(user_id)
        except (InvalidId, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
            )

        # Find user in database
        user = await db.users.find_one({"_id": user_oid})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if the refresh token matches the one in database
        if user.get("refresh_token") != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Generate new tokens
        now = datetime.now()
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        new_refresh_token = create_access_token(
            data={"sub": user_id, "type": "refresh"},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        # Update refresh token in DB
        await db.users.update_one(
            {"_id": user_oid},
            {"$set": {"refresh_token": new_refresh_token, "updated_at": now}},
        )

        # Prepare user response
        user_response = UserResponse(
            id=user_id,
            email=user["email"],
            is_admin=user.get("is_admin", False),
            representative_id=str(user.get("representative_id")),
            created_at=user.get("created_at"),
            updated_at=now,
        )

        return UserToken(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response,
        )

    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


async def change_password_service(
    user_id: ObjectId,
    current_password: str,
    new_password: str,
    db,
):
    user = await db.users.find_one({"_id": user_id})
    if not user or not verify_password(current_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    if verify_password(new_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )
    hashed_new_password = hash_password(new_password)
    now = datetime.now()
    await db.users.update_one(
        {"_id": user_id}, {"$set": {"password": hashed_new_password, "updated_at": now}}
    )
    return {"message": "Password updated successfully"}


async def admin_reset_password_service(
    target_user_id: ObjectId,
    new_password: str,
    db,
):
    user = await db.users.find_one({"_id": target_user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    hashed_new_password = hash_password(new_password)
    now = datetime.now()
    await db.users.update_one(
        {"_id": target_user_id},
        {"$set": {"password": hashed_new_password, "updated_at": now}},
    )
    return {"message": "Password reset successfully"}


async def delete_account_service(
    target_user_id: ObjectId,
    db,
):
    result = await db.users.delete_one({"_id": target_user_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"message": "Account deleted successfully"}


async def get_all_users_service(db) -> List[UserResponse]:
    """
    Fetch all users from the database and return as a list of UserResponse.
    """
    users_cursor = db.users.find({})
    users = []
    async for user in users_cursor:
        users.append(
            UserResponse(
                id=str(user["_id"]),
                email=user["email"],
                is_admin=user.get("is_admin", False),
                representative_id=str(user.get("representative_id")),
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at"),
            )
        )
    return users

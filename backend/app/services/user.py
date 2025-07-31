import secrets
from datetime import datetime, timedelta
from typing import List

from app.core.config import settings
from app.models.user import UserCreate, UserResponse, UserToken
from app.utils.security import create_access_token, hash_password, verify_password
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_user_service(user: UserCreate, db: AsyncIOMotorDatabase) -> UserToken:
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user and secrets.compare_digest(existing_user["email"], user.email):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(user.password)

    # Prepare user document
    now = datetime.now()
    user_doc = {
        "email": user.email,
        "password": hashed_password,
        "is_admin": user.is_admin,
        "rep_id": user.rep_id,
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
        rep_id=user.rep_id,
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
        rep_id=user.get("rep_id"),
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


async def change_password_service(
    user_id: ObjectId,
    current_password: str,
    new_password: str,
    db,
):
    user = await db.users.find_one({"_id": user_id})
    print(user)
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
                rep_id=user.get("rep_id"),
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at"),
            )
        )
    return users

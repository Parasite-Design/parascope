from typing import List

from app.core.database import get_db
from app.models.user import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    LoginRequest,
    UserCreate,
    UserResponse,
    UserToken,
)
from app.services.user import (
    admin_reset_password_service,
    change_password_service,
    create_user_service,
    delete_account_service,
    get_all_users_service,
    login_user_service,
    logout_user_service,
    refresh_token_service,
)
from app.utils.security import admin_required, get_current_user
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.post("/register", response_model=UserToken)
async def create_user(
    user: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(admin_required),
):
    return await create_user_service(user, db)


@router.post("/login", response_model=UserToken)
async def login_user(
    login_data: LoginRequest = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await login_user_service(login_data.email, login_data.password, db)  # pyright: ignore[reportArgumentType]


@router.post("/logout", response_model=dict, status_code=status.HTTP_200_OK)
async def logout_user(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint for users to log out (invalidate refresh token).
    """
    try:
        user_object_id = ObjectId(current_user.id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
        )
    return await logout_user_service(user_object_id, db)


@router.post("/refresh", response_model=UserToken)
async def refresh_token(
    refresh_data: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """
    Endpoint to refresh access token using a valid refresh token.
    """
    refresh_token = refresh_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token is required"
        )

    return await refresh_token_service(refresh_token, db)


@router.get("/validate", response_model=dict)
async def validate_token(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint to validate if a token is still valid.
    """
    return {"valid": True, "user": current_user}


@router.get("/is-admin", response_model=dict)
async def is_admin(
    current_user: UserResponse = Depends(admin_required),
):
    """
    Endpoint to check if the current user is an admin.
    Returns: {"is_admin": true}
    """
    return {"is_admin": current_user.is_admin}


@router.post("/change-password", response_model=dict, status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint for authenticated users to change their password.
    """
    try:
        user_object_id = ObjectId(current_user.id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
        )
    return await change_password_service(
        user_id=user_object_id,
        current_password=data.current_password,
        new_password=data.new_password,
        db=db,
    )


@router.post("/reset-password", response_model=dict, status_code=status.HTTP_200_OK)
async def admin_reset_password(
    data: AdminResetPasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(admin_required),
):
    """
    Admin endpoint to reset any user's password.
    """
    try:
        target_user_object_id = ObjectId(data.user_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target user ID"
        )
    return await admin_reset_password_service(
        target_user_id=target_user_object_id,
        new_password=data.new_password,
        db=db,
    )


@router.delete("/delete-account", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_account(
    user_id: str = Query(default=None, description="User ID to delete (admin only)"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Endpoint for users to delete their own account.
    Admins can delete any account by providing user_id.
    """
    if current_user.is_admin and user_id:
        try:
            target_user_object_id = ObjectId(user_id)
        except (InvalidId, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target user ID"
            )
        return await delete_account_service(target_user_id=target_user_object_id, db=db)
    else:
        try:
            user_object_id = ObjectId(current_user.id)
        except (InvalidId, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
            )
        return await delete_account_service(target_user_id=user_object_id, db=db)


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserResponse = Depends(admin_required),
):
    """
    Admin endpoint to retrieve all registered users.
    """
    return await get_all_users_service(db)

from app.core.database import get_db
from app.models.user import LoginRequest, UserCreate, UserResponse, UserToken
from app.services.user import create_user_service, login_user_service
from app.utils.security import admin_required
from fastapi import APIRouter, Body, Depends
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


@router.get("/is-admin", response_model=dict)
async def is_admin(
    current_user: UserResponse = Depends(admin_required),
):
    """
    Endpoint to check if the current user is an admin.
    Returns: {"is_admin": true}
    """
    return {"is_admin": current_user.is_admin}

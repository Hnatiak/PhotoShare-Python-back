from fastapi import APIRouter, HTTPException, Depends, status, File, Form, UploadFile, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas.user import UserResponse
from src.schemas.schemas import UserResponseAll
from src.services.auth import auth_service

from src.repository import users as repositories_users
from src.database.db import get_db

router = APIRouter(prefix='/users', tags=['users'])

@router.get("/me", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    return user

@router.post("/edit-me", response_model=UserResponse)
async def edit_my_profile(avatar: UploadFile = File(), new_username: str = Form(None), user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)):
    updated_user = await repositories_users.edit_my_profile(avatar, new_username, user, db)
    return updated_user

@router.get("/all", response_model=UserResponseAll)
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users = await repositories_users.get_all_users(db)
    return {"users": users}
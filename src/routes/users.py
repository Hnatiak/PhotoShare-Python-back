from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas.user import UserResponse
from src.services.auth import auth_service

router = APIRouter(prefix='/users', tags=['users'])

@router.get("/me", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """
    The get_current_user function is used to get the current user.

    :param user: User: Get the current user
    :return: The current user
    """
    return user


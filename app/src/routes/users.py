from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Path,
    status,
    File,
    Form,
    UploadFile,
    Query,
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List
from sqlalchemy.orm import Session

from src.entity.models import User, Role

from src.schemas.schemas import UserResponse, UserUpdateSchema, UserDb, RoleUpdateSchema, SearchUserResponse
from src.services.auth import auth_service

from src.repository import users as repositories_users
from src.database.db import get_db
from src.services.roles import RoleChecker

import cloudinary
import cloudinary.uploader


router = APIRouter(prefix="/users", tags=["users"])

allowed_get_all_users = RoleChecker([Role.admin])


@router.get(
    "/me",
    response_model=SearchUserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """
    The get_current_user function is a dependency that returns the current user.
    Args:
        user:

    Returns:

    """
    return user


# @router.post("/edit-me", response_model=UserResponse)
# async def edit_my_profile(avatar: UploadFile = File(), new_username: str = Form(None), user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)):
#     updated_user = await repositories_users.edit_my_profile(avatar, new_username, user, db)
#     return updated_user


@router.put("/")
async def update_user(
    body: UserUpdateSchema,
    db: AsyncSession = Depends(get_db),
    cur_user: User = Depends(auth_service.get_current_user),
):
    """
    The update_user function updates a user's information.
    Args:
        body:
        db:
        cur_user:

    Returns:

    """
    user = await repositories_users.update_user(cur_user.id, body, db)
    if cur_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not Found",
        )
    return user


@router.put("/avatar")
async def update_avatar(
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The update_avatar function updates the avatar of a user.
    Args:
        file:
        current_user:
        db:

    Returns:

    """
    r = cloudinary.uploader.upload(
        file.file, public_id=f"NotesApp/{current_user.username}", overwrite=True
    )
    src_url = cloudinary.CloudinaryImage(f"NotesApp/{current_user.username}").build_url(
        width=250, height=250, crop="fill", version=r.get("version")
    )
    user = await repositories_users.update_avatar(current_user.email, src_url, db)
    return user


@router.get(
    "/all",
    response_model=List[SearchUserResponse],
    # dependencies=[Depends(allowed_get_all_users)],
)
async def read_all_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    The read_all_users function returns a list of users.
    Args:
        skip:
        limit:
        db:

    Returns:

    """
    users = await repositories_users.get_users(skip, limit, db)
    return users


@router.get("/{user_id}", response_model=SearchUserResponse)
async def get_user(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    cur_user: User = Depends(auth_service.get_current_user),
):
    """
    The get_user function is used to get a user.
    Args:
        user_id:
        db:
        cur_user:

    Returns:

    """
    user = await repositories_users.get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put(
    "/role/{user_id}",
    response_model=SearchUserResponse,
)
async def change_role(
    user_id: int,    
    role: Role,
    db: AsyncSession = Depends(get_db),
    cur_user: User = Depends(auth_service.get_current_user),
):
    """
    The change_role function is used to change the role of a user.
    Args:
        user_id:
        body:
        db:
        cur_user:

    Returns:

    """
    if cur_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission chandge role",
        )
    user = await repositories_users.change_role(user_id, body, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user

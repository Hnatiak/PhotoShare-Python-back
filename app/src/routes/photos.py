import uuid
from typing import List
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pydantic_core import PydanticCustomError
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter
from src.database.db import get_db
from src.database.models import User
from src.repository import photos as repository_photos
from src.services.auth import auth_service
from fastapi import APIRouter, Form, HTTPException, Depends, status, UploadFile, File
from src.schemas import PhotoBase, PhotoResponse
from src.conf.config import settings

router = APIRouter(prefix='/photos', tags=["photos"])
rl_times = settings.rate_limiter_times
rl_seconds = settings.rate_limiter_seconds

def checker(data: str = Form(...)) -> PhotoBase:
    try:
        return PhotoBase.model_validate_json(data)
    except ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

@router.get("/", response_model=List[PhotoResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def read_photos(filter: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    photos = await repository_photos.get_photos(filter, skip, limit, current_user, db)    
    return photos


@router.get("/{photo_id}", response_model=PhotoResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def read_photo(photo_id: uuid.UUID, db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    photo = await repository_photos.get_photo(photo_id, current_user, db)
    return photo


@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def create_photo(file: UploadFile = File(), photo_description: str = Form(None), tags: list[str] = Form([]), db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    body: PhotoBase = None 
    try:
        body = PhotoBase(description=photo_description, tags=tags[0].split(','))
    except ValidationError as err:
        raise HTTPException(
                detail=jsonable_encoder(err.errors()),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    photo = await repository_photos.create_photo(file, body, current_user, db)
    return photo


@router.delete("/{photo_id}", response_model=PhotoResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def remove_photo(photo_id: uuid.UUID, db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    photo = await repository_photos.remove_photo(photo_id, current_user, db)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo

@router.put("/{photo_id}", response_model=PhotoResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def update_photo_details(photo_id: uuid.UUID, photo_description: str = Form(None), tags: list[str] = Form([]), db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    photo = None
    try:
        body = PhotoBase(description=photo_description, tags=tags[0].split(','))    
        photo = await repository_photos.update_photo_details(photo_id, body, current_user, db)
    except ValidationError as err:
        raise HTTPException(
                detail=jsonable_encoder(err.errors()),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    except IndexError as err:
        raise HTTPException(
                detail=jsonable_encoder(err.args[0]),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo
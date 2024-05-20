import base64
import io
import uuid
from typing import List
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter
from src.database.db import get_db
from src.entity.models import User, AssetType, Role
from src.repository import photos as repository_photos, qrcode as repository_qrcode
from src.services.auth import auth_service
from src.services.photo import CloudPhotoService
from fastapi import APIRouter, Form, HTTPException, Depends, status, UploadFile, File
from src.schemas.schemas import PhotoBase, PhotoResponse, LinkType
from src.conf.config import settings
from src.repository.exceptions import AccessDeniedException


router = APIRouter(prefix="/photos", tags=["photos"])
rl_times = settings.rate_limiter_times
rl_seconds = settings.rate_limiter_seconds


##############################
async def is_operaation_restricted_to_user(
    current_user: User = Depends(auth_service.get_current_user)
) -> bool:    
    return current_user.role != Role.admin

##############################


@router.get(
    "/",
    response_model=List[PhotoResponse],
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))]
)
async def read_photos(
    filter: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    photos = await repository_photos.get_photos(filter, skip, limit, current_user, db)
    return photos


@router.get(
    "/{photo_id}",
    response_model=PhotoResponse,
    description="No more than 10 requests per minute",
    dependencies=[
        Depends(RateLimiter(times=rl_times, seconds=rl_seconds))
    ]
)
async def read_photo(
    photo_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    photo = await repository_photos.get_photo(photo_id, current_user, db)    
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )
    return photo


@router.get(
    "/link/{photo_id}",
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))]
)
async def read_photo(
    photo_id: uuid.UUID,
    link_type: LinkType,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    photo = await repository_photos.get_photo(photo_id, current_user, db)
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )
    if link_type.name == LinkType.url.name:
        return photo.url
    qr_code = await repository_qrcode.read_qr_code(
        photo_id=photo.id, user=current_user, db=db
    )
    if qr_code:
        return StreamingResponse(qr_code, media_type="image/png")
    return ""


@router.post(
    "/",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))]
)
async def create_photo(
    file: UploadFile = File(),
    photo_description: str = Form(None),
    tags: list[str] = Form([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    photo = None
    try:
        public_id = f"{settings.cloudinary_app_prefix}/{CloudPhotoService.get_unique_file_name(file.filename)}"
        asset = CloudPhotoService.upload_photo(file=file, public_id=public_id)
        url = CloudPhotoService.get_photo_url(public_id=public_id, asset=asset)
        body = PhotoBase(
            url=url, description=photo_description, tags=tags[0].split(",")
        )
        photo = await repository_photos.create_photo(body, current_user, db)
        # qr_code_binary = generate_qrcode(photo.url)
        # await repository_qrcode.save_qr_code(photo_id=photo.id, qr_code_binary=qr_code_binary, user=current_user, db=db)
    except ValidationError as err:
        raise HTTPException(
            detail=jsonable_encoder(err.errors()),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return photo


@router.post(
    "/transform/{photo_id}",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))]
)
async def transform_photo(
    photo_id: uuid.UUID,
    transformation: AssetType,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    photo = None
    try:
        # photo = await repository_photos.get_photo(photo_id, current_user, db)
        photo = await repository_photos.get_photo(photo_id, db)
        if photo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
            )
        if photo.asset_type != AssetType.origin:
            raise HTTPException(
                detail="Can't transform due to this photo has already been transformed",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        transformated_url = CloudPhotoService.transformate_photo(
            photo.url, transformation
        )
        photo = await repository_photos.create_transformation(
            url=transformated_url,
            description=photo.description,
            tags=photo.tags,
            asset_type=transformation,
            user=current_user,
            db=db,
        )
        # qr_code_binary = generate_qrcode(photo.url)
        # await repository_qrcode.save_qr_code(photo_id=photo.id, qr_code_binary=qr_code_binary, user=current_user, db=db)
    except HTTPException as err:
        raise err
    except Exception as err:
        raise HTTPException(
            detail=jsonable_encoder(err.args),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return photo


@router.delete(
    "/{photo_id}",
    response_model=PhotoResponse,
    description="No more than 10 requests per minute",
    dependencies=[
        Depends(RateLimiter(times=rl_times, seconds=rl_seconds))
    ]
)
async def remove_photo(
    photo_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    is_restricted_to_user: bool = Depends(is_operaation_restricted_to_user)
):  
    photo = None
    try:
        photo = await repository_photos.remove_photo(photo_id, current_user, db, is_restricted_to_user)
    except AccessDeniedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission for CRUD on this photo"
        )
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Photo not found"
        )
    return photo


@router.put(
    "/{photo_id}",
    response_model=PhotoResponse,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))]
)
async def update_photo_details(
    photo_id: uuid.UUID,
    photo_description: str = Form(None),
    tags: list[str] = Form([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    is_restricted_to_user: bool = Depends(is_operaation_restricted_to_user)
):
    photo = None
    try:
        body = PhotoBase(description=photo_description, tags=tags[0].split(","))
        photo = await repository_photos.update_photo_details(
            photo_id, body, current_user, db, is_restricted_to_user
        )
    except AccessDeniedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission for CRUD on this photo"
        )
    except ValidationError as err:
        raise HTTPException(
            detail=jsonable_encoder(err.errors()),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except IndexError as err:
        raise HTTPException(
            detail=jsonable_encoder(err.args),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )
    return photo

import logging
import uuid
from typing import Annotated, List
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter
import uvicorn
from src.database.db import get_db
from src.entity.models import User, Role, AssetType as model_asset_type
from src.repository.photos import repository_photos 
from src.repository.qrcode import repository_qrcode
from src.services.auth import auth_service
from src.services.photo import CloudPhotoService
from src.services.qrcode import qrcode_service
from src.services.authorization import AccessRule as access_rule, Authorization as authorization_service
from fastapi import APIRouter, Form, HTTPException, Depends, Path, Query, status, UploadFile, File
from src.schemas.schemas import PhotoBase, PhotoResponse, LinkType, PhotoUpdate, Operation, AssetType
from src.conf.config import settings
from src.exceptions.exceptions import AccessDeniedException


logger = logging.getLogger(uvicorn.logging.__name__)
router = APIRouter(prefix="/photos", tags=["photos"])
rl_times = settings.rate_limiter_times
rl_seconds = settings.rate_limiter_seconds


@router.get("/", response_model=List[PhotoResponse], 
            description="No more than 10 requests per minute",
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def read_photos(keyword: str =  Query(default=None, description="Search photo by keyword in description"),
                        tag: str =  Query(default=None, description="Search photo by tag"),
                        skip: int = Query(default=0, ge=0, description="Records to skip in response"),
                        limit: int = Query(default=20, ge=1, le=50, description="Records per response to show"),
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        authorization: authorization_service = Depends(authorization_service(
                                    [
                                        access_rule(Operation.read, [Role.user, Role.moderator, Role.admin])
                                    ]
                                ).authorize)
                    ):
    """
    Retrieves a list of photos based on provided search criteria.

    **Rate Limit:** 10 requests per minute

    Args:
        keyword: Optional keyword to search photos by description (default: None)
        tag: Optional tag to search photos by (default: None)
        skip: Number of records to skip in the response (default: 0)
        limit: Number of records to include in the response (default: 20, max: 50)
        db: Database session dependency
        current_user: Currently authenticated user dependency
        authorization: Authorization service dependency
    Returns:
        List of photo response objects
    Raises:
        HTTPException: 403 Forbidden if user lacks permissions to perform read operation
    """    
    permissions = authorization.check_entity_permissions()
    if not permissions[0]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permissions for {', '.join(permissions[1])} operation")
    photos = await repository_photos.get_photos(keyword=keyword, tag=tag, skip=skip, limit=limit, user=current_user, db=db)
    return photos


@router.get("/{photo_id}", response_model=PhotoResponse, 
            description="No more than 10 requests per minute",
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def read_photo(photo_id: uuid.UUID,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        authorization: authorization_service = Depends(authorization_service(
                                    [
                                        access_rule(Operation.read, [Role.user, Role.moderator, Role.admin])
                                    ]
                                ).authorize)
                    ):
    """
    Retrieves a single photo by its unique identifier.

    **Rate Limit:** 10 requests per minute

    Args:
        photo_id: Unique identifier of the photo to retrieve
        db: Database session dependency
        current_user: Currently authenticated user dependency
        authorization: Authorization service dependency
    Returns:
        Photo response object
    Raises:
        HTTPException: 404 Not Found if photo with specified ID is not found
        HTTPException: 403 Forbidden if user lacks permissions to perform read operation
    """
    photo = await repository_photos.get_photo(photo_id=photo_id, user=current_user, db=db)    
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    permissions = authorization.check_entity_permissions(photo.user)
    if not permissions[0]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permissions for {', '.join(permissions[1])} operation")
    return photo


@router.get("/link/{photo_id}", description="No more than 10 requests per minute",
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def read_photo(photo_id: uuid.UUID,
                        link_type: LinkType = LinkType.qr_code,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        authorization: authorization_service = Depends(authorization_service(
                                    [
                                        access_rule(Operation.read, [Role.user, Role.moderator, Role.admin])
                                    ]
                                ).authorize)
                    ):
    """
    Retrieves generated QR code or unique link for photo by its unique identifier.

    **Rate Limit:** 10 requests per minute

    Args:
        photo_id: Unique identifier of the photo to retrieve
        link_type: Type of link to retrieve (default: qr_code)
        db: Database session dependency
        current_user: Currently authenticated user dependency
        authorization: Authorization service dependency
    Returns:
        Photo URL if link_type is LinkType.url, otherwise a StreamingResponse containing QR code image
    Raises:
        HTTPException: 404 Not Found if photo with specified ID is not found
        HTTPException: 403 Forbidden if user lacks permissions to perform read operation
    """        
    photo = await repository_photos.get_photo(photo_id=photo_id, user=current_user, db=db)    
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    permissions = authorization.check_entity_permissions(photo.user)
    if not permissions[0]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permissions for {', '.join(permissions[1])} operation")
    if link_type.name == LinkType.url.name:
        return photo.url
    qr_code = await repository_qrcode.read_qrcode(photo_id=photo.id, user=current_user, db=db)
    if qr_code:
        return StreamingResponse(content=qr_code, media_type="image/png")
    return ""


@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED,
             description="No more than 10 requests per minute", 
             dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def create_photo(file: UploadFile = File(),
                        description: str = Form(default=None, min_length=1, max_length=500, description="Photo description"),
                        tags: list[str] = Form(default=[], description="Up to 5 tags"),
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        authorization: authorization_service = Depends(authorization_service(
                                    [                                        
                                        access_rule(Operation.create, [Role.user, Role.moderator, Role.admin])
                                    ]
                                ).authorize)
                    ):
    """
    Creates a new photo record and uploads the associated image file.

    **Rate Limit:** 10 requests per minute

    Args:
        file: Image file upload (required)
        description: Description of the photo (default: None, min length 1, max length 500)
        tags: List of tags associated with the photo (default: [])
        db: Database session dependency
        current_user: Currently authenticated user dependency
        authorization: Authorization service dependency
    Returns:
        Photo response object
    Raises:
        HTTPException: 400 Bad Request if validation error occurs or photo has already been transformed
        HTTPException: 403 Forbidden if user lacks permissions to create photos
    """

    photo = None
    try:
        permissions = authorization.check_entity_permissions()
        if not permissions[0]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permissions for {', '.join(permissions[1])} operation")
        public_id = f"{settings.cloudinary_app_prefix}/{CloudPhotoService.get_unique_file_name(filename=file.filename)}"
        asset = CloudPhotoService.upload_photo(file=file, public_id=public_id)
        url = CloudPhotoService.get_photo_url(public_id=public_id, asset=asset)
        body = PhotoBase(url=url, description=description, tags=tags[0].split(","))
        photo = await repository_photos.create_photo(body=body, user=current_user, db=db)
        qr_code_binary = qrcode_service.generate_qrcode(url=photo.url)
        await repository_qrcode.save_qrcode(photo_id=photo.id, qr_code_binary=qr_code_binary, user=current_user, db=db)
    except ValidationError as err:
        raise HTTPException(detail=jsonable_encoder(err.errors()), status_code=status.HTTP_400_BAD_REQUEST)    
    return photo


@router.post("/transform/{photo_id}", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def transform_photo(photo_id: uuid.UUID,
                        transformation: AssetType = None,                        
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        authorization: authorization_service = Depends(authorization_service(
                                    [
                                        access_rule(Operation.read, [Role.user, Role.moderator, Role.admin]),
                                        access_rule(Operation.create, [Role.user, Role.moderator, Role.admin])
                                    ]
                                ).authorize)
                    ):
    """
    Creates a transformed version of an existing photo.

    **Rate Limit:** 10 requests per minute

    Args:
        photo_id: Unique identifier of the photo to transform
        transformation: Transformation type to apply (default: origin)
        db: Database session dependency
        current_user: Currently authenticated user dependency
        authorization: Authorization service dependency
    Returns:
        Photo response object representing the transformed photo
    Raises:
        HTTPException: 404 Not Found if photo with specified ID is not found
        HTTPException: 403 Forbidden if user lacks permissions to perform read or create operation
        HTTPException: 400 Bad Request if photo has already been transformed
    """
    photo = None
    if not transformation:
        raise HTTPException(detail="Transformation option is not selected",
                                status_code=status.HTTP_400_BAD_REQUEST)
    try:
        photo = await repository_photos.get_photo(photo_id=photo_id, user=current_user, db=db)    
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        permissions = authorization.check_entity_permissions()
        if not permissions[0]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permissions for {', '.join(permissions[1])} operation")
        if photo.asset_type != model_asset_type.origin:
            raise HTTPException(detail="Can't transform because of this photo has already been transformed",
                                status_code=status.HTTP_400_BAD_REQUEST)
        asset_type_option = model_asset_type[transformation.name]
        transformated_url = CloudPhotoService.transformate_photo(url=photo.url, asset_type=transformation)
        photo = await repository_photos.create_transformation(url=transformated_url,
                                                              description=photo.description,
                                                              tags=photo.tags,
                                                              asset_type=asset_type_option,
                                                              user=current_user,
                                                              db=db)
        qr_code_binary = qrcode_service.generate_qrcode(url=photo.url)
        await repository_qrcode.save_qrcode(photo_id=photo.id, qr_code_binary=qr_code_binary, user=current_user, db=db)
    except HTTPException as err:
        raise err
    except Exception as err:
        raise HTTPException(detail=jsonable_encoder(err.args), status_code=status.HTTP_400_BAD_REQUEST)
    return photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def remove_photo(photo_id: uuid.UUID,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        authorization: authorization_service = Depends(authorization_service(
                                    [
                                        access_rule(Operation.read, [Role.user, Role.moderator, Role.admin]),
                                        access_rule(Operation.delete, [Role.admin])
                                    ]
                                ).authorize)
                    ):
    """
    Deletes a photo record and its associations.

    **Rate Limit:** 10 requests per minute

    Args:
        photo_id: Unique identifier of the photo to delete
        db: Database session dependency
        current_user: Currently authenticated user dependency
        authorization: Authorization service dependency
    Returns:
        None
    Raises:
        HTTPException: 404 Not Found if photo with specified ID is not found
        HTTPException: 403 Forbidden if user lacks permissions to perform delete operation
    """  
    photo = await repository_photos.get_photo(photo_id=photo_id, user=current_user, db=db, disable_caching=True)    
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    permissions = authorization.check_entity_permissions(photo.user)
    if not permissions[0]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permissions for {', '.join(permissions[1])} operation")
    photo = await repository_photos.remove_photo(photo=photo, user=current_user, db=db)
    return None


@router.put("/{photo_id}", response_model=PhotoResponse,
            description="No more than 10 requests per minute",
            dependencies=[Depends(RateLimiter(times=rl_times, seconds=rl_seconds))])
async def update_photo_details(photo_id: uuid.UUID,
                                photo_description: str = Form(None),
                                tags: list[str] = Form([]),
                                db: Session = Depends(get_db),
                                current_user: User = Depends(auth_service.get_current_user),
                                authorization: authorization_service = Depends(authorization_service(
                                    [
                                        access_rule(Operation.read, [Role.user, Role.moderator, Role.admin]),
                                        access_rule(Operation.write, [Role.admin])
                                    ]
                                ).authorize)
                            ):
    """
    Updates the description and tags associated with a photo.

    **Rate Limit:** 10 requests per minute

    Args:
        photo_id: Unique identifier of the photo to update
        photo_description: Updated description of the photo (optional)
        tags: Updated list of tags associated with the photo (default: [])
        db: Database session dependency
        current_user: Currently authenticated user dependency
        authorization: Authorization service dependency
    Returns:
        Photo response object reflecting the updated photo details
    Raises:
        HTTPException: 404 Not Found if photo with specified ID is not found
        HTTPException: 403 Forbidden if user lacks permissions to perform read or write operation
        HTTPException: 400 Bad Request if validation error occurs (e.g. empty tags list)
    """
    photo = None
    try:
        photo = await repository_photos.get_photo(photo_id=photo_id, user=current_user, db=db, disable_caching=True)    
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        permissions = authorization.check_entity_permissions(photo.user)
        if not permissions[0]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You don't have permissions for {', '.join(permissions[1])} operation")
        body = PhotoUpdate(description=photo_description, tags=tags[0].split(",") if tags else [])        
        photo = await repository_photos.update_photo_details(photo=photo, 
                                                             body=body, 
                                                             user=current_user, 
                                                             db=db)    
    except ValidationError as err:
        raise HTTPException(detail=jsonable_encoder(err.errors()), status_code=status.HTTP_400_BAD_REQUEST)
    except IndexError as err:
        raise HTTPException(detail=jsonable_encoder(err.args), status_code=status.HTTP_400_BAD_REQUEST)    
    return photo

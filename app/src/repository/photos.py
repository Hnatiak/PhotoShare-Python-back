import uuid
from typing import List
from sqlalchemy import func, and_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.relationships import _RelationshipDeclared
from sqlalchemy.orm.properties import ColumnProperty
from fastapi import UploadFile
from src.entity.models import Photo, Tag, User, AssetType
from datetime import datetime, timedelta
from src.schemas.schemas import PhotoBase, PhotoResponse
from src.repository.exceptions import AccessDeniedException


async def get_photos(filter: str | None, skip: int, limit: int, user: User, db: Session) -> List[Photo]:
    query = db.query(Photo)
    filters = parse_filter(filter)
    for attr, value in filters.items():
        if isinstance(getattr(Photo, attr).property, ColumnProperty):
            search = "%{}%".format(value.lower())
            query = query.filter(func.lower(getattr(Photo, attr)).like(search))
        elif isinstance(getattr(Photo, attr).property, _RelationshipDeclared):
            query = query.filter(getattr(Photo, attr).any(func.lower(Tag.name) == value.lower()))
    query = query.offset(skip).limit(limit)
    return query.all()


async def get_photo(id:uuid.UUID, user: User, db: Session) -> Photo:
    query = db.query(Photo).filter(Photo.id == id)
    return query.first()

# tag::sometag|description::keyword
def parse_filter(filter: str | None) -> dict:
    if filter:
        lst = filter.split("|")
        dct = {}
        for f in lst:
            key, value = f.split("::")
            dct[key] = value
        return dct
    return {}


async def ensure_tags(tags: list[str], db: Session) -> list[Tag]:
    ensured_tags = []
    if tags:
        for tag in set(tags):
            if tag:
                existing_tag = db.query(Tag).filter(Tag.name == tag).first()
                if not existing_tag:
                    existing_tag = Tag(name=tag)
                    db.add(existing_tag)
                    db.commit()
                    db.refresh(existing_tag)
                ensured_tags.append(existing_tag)
    return list(set(ensured_tags))


async def create_photo(body: PhotoBase, user: User, db: Session) -> Photo:    
    tags = await ensure_tags(tags=body.tags, db=db)
    photo = Photo(
            description=body.description, 
            tags=tags, 
            url=body.url,
            asset_type=AssetType.origin,
            user = user
            )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo

async def create_transformation(url: str, description: str, tags: list[Tag], asset_type: AssetType, user: User, db: Session) -> Photo:    
    photo = Photo(
            description=description, 
            tags=tags, 
            url=url,
            asset_type=asset_type,
            user = user
            )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


async def remove_photo(photo_id: uuid.UUID, user: User, db: Session, is_restricted: bool) -> Photo | None:
    query = db.query(Photo)    
    query = query.filter(Photo.id == photo_id)
    photo = query.first()
    if not photo:
        return None
    if is_restricted and photo.user_id != user.id:
        raise AccessDeniedException    
    
    if photo:
        db.delete(photo)
        db.commit()
    return photo


async def update_photo_details(photo_id: uuid.UUID, body: PhotoBase, user: User, db: Session, is_restricted: bool) -> Photo | None:
    query = db.query(Photo)
    query = query.filter(Photo.id == photo_id)
    photo = query.first()      
    if not photo:
        return None
    if is_restricted and photo.user_id != user.id:
        raise AccessDeniedException    
    
    tags = [tag for tag in body.tags if not any(t.name == tag for t in photo.tags)]    
    if len(photo.tags) + len(tags) > 5:
        raise IndexError(f"Maximum number of tags per photo is 5, and this photo already has {len(photo.tags)} tags.")    
    if body.description:
        photo.description = body.description
    if tags:
        photo.tags += await ensure_tags(tags=tags, db=db)
    db.add(photo)
    db.commit()
    return photo

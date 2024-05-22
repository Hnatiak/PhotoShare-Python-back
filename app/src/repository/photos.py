import uuid
import logging
import uvicorn.logging
from typing import List
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload, Query
from src.entity.models import Photo, Tag, User, AssetType
from datetime import datetime, timedelta
from src.schemas.schemas import PhotoBase, PhotoResponse, PhotoUpdate
from src.repository.exceptions import AccessDeniedException
from src.services.cache import QueryExecutor, CacheableQuery, CacheableQueryExecutor


logger = logging.getLogger(uvicorn.logging.__name__)


class PhotosRepository:
    def __init__(self, query_executor: QueryExecutor = None) -> None:
        self.query_executor = query_executor

    async def __all(self, query:Query):
        if self.query_executor:            
            return await self.query_executor.get_all(query=query)
        return query.all()
    
    async def __first(self, id_key, query:Query):
        if self.query_executor:
            return await self.query_executor.get_first(id_key=id_key, query=query)
        return query.first()


    async def get_photos(self, keyword: str | None, tag: str | None, skip: int, limit: int, user: User, db: Session) -> List[Photo]:
        query = db.query(Photo)  
        filters = []
        if keyword:
            filters.append(func.lower(Photo.description).like(f"%{keyword.lower()}%"))
        if tag:
            filters.append(Photo.tags.any(func.lower(Tag.name) == tag.lower()))
        query = query.filter(or_(*filters))
        query = query.offset(skip).limit(limit)
        return await self.__all(query=query)


    async def get_photo(self, photo_id:uuid.UUID, user: User, db: Session) -> Photo:
        query = db.query(Photo).filter(Photo.id == photo_id)
        return await self.__first(id_key=photo_id, query=query)


    def __parse_filter(self, filter: str | None) -> dict:
        if filter:
            lst = filter.split("|")
            dct = {}
            for f in lst:
                key, value = f.split("::")
                dct[key] = value
            return dct
        return {}


    async def __ensure_tags(self, tags: list[str], db: Session) -> list[Tag]:
        ensured_tags = []
        if tags:
            for tag in set(tags):
                if tag:                    
                    query = db.query(Tag).filter(Tag.name == tag)
                    existing_tag = await self.__first(id_key=tag, query=query)
                    if not existing_tag:
                        existing_tag = Tag(name=tag)
                        db.add(existing_tag)
                        db.commit()
                        db.refresh(existing_tag)
                    ensured_tags.append(existing_tag)
        return list(set(ensured_tags))


    async def create_photo(self, body: PhotoBase, user: User, db: Session) -> Photo:    
        tags = await self.__ensure_tags(tags=body.tags, db=db)
        photo = Photo(description=body.description, 
                    tags=tags, 
                    url=body.url,
                    asset_type=AssetType.origin,
                    user = user)
        db.add(photo)
        db.commit()
        db.refresh(photo)
        if isinstance(self.query_executor, CacheableQuery):
            await self.query_executor.invalidate_cache_for_all()
        return photo


    async def create_transformation(self, url: str, description: str, tags: list[Tag], asset_type: AssetType, user: User, db: Session) -> Photo:    
        photo = Photo(description=description, 
                    tags=tags, 
                    url=url,
                    asset_type=asset_type,
                    user = user)
        db.add(photo)
        db.commit()
        db.refresh(photo)
        if isinstance(self.query_executor, CacheableQuery):
            await self.query_executor.invalidate_cache_for_all()
        return photo


    async def remove_photo(self, photo_id: uuid.UUID, user: User, db: Session, is_restricted: bool) -> Photo | None:
        query = db.query(Photo)    
        query = query.filter(Photo.id == photo_id)
        photo = await self.__first(id_key=photo_id, query=query)
        if not photo:
            return None
        if is_restricted and photo.user_id != user.id:
            raise AccessDeniedException    
        
        if photo:
            db.delete(photo)
            db.commit()
            if isinstance(self.query_executor, CacheableQuery):
                await self.query_executor.invalidate_cache_for_all()
                await self.query_executor.invalidate_cache_for_first(photo_id)
        return photo


    async def update_photo_details(self, photo_id: uuid.UUID, body: PhotoUpdate, user: User, db: Session, is_restricted: bool) -> Photo | None:
        query = db.query(Photo)
        query = query.filter(Photo.id == photo_id)
        photo = await self.__first(id_key=photo_id, query=query)      
        if not photo:
            return None
        if is_restricted and photo.user_id != user.id:
            raise AccessDeniedException    
        db.commit()
        tags = [tag for tag in body.tags if not any(t.name == tag for t in photo.tags)]    
        if len(photo.tags) + len(tags) > 5:
            raise IndexError(f"Maximum number of tags per photo is 5, and this photo already has {len(photo.tags)} tags.")    
        if body.description:
            photo.description = body.description
        if tags:
            photo.tags += await self.__ensure_tags(tags=tags, db=db)
        db.add(photo)
        db.commit()
        if isinstance(self.query_executor, CacheableQuery):
            await self.query_executor.invalidate_cache_for_all()
            await self.query_executor.invalidate_cache_for_first(photo_id)
        return photo


repository_photos = PhotosRepository(query_executor=CacheableQueryExecutor())
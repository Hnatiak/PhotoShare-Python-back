import uuid
import logging
import uvicorn.logging
from typing import List
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, Query
from src.entity.models import Photo, Tag, User, AssetType
from datetime import datetime, timedelta
from src.schemas.schemas import PhotoBase, PhotoUpdate
from src.exceptions.exceptions import AccessDeniedException
from src.services.cache import QueryExecutor, CacheableQuery, CacheableQueryExecutor


logger = logging.getLogger(uvicorn.logging.__name__)


class PhotosRepository:
    """
    Provides data access operations for Photo entities.

    This class is responsible for interacting with the database to perform CRUD (Create, Read, Update, Delete)
    operations on Photo records, as well as managing their associated tags. It leverages a query executor
    for potential caching of queries.
    """
    def __init__(self, query_executor: QueryExecutor = None) -> None:
        self.query_executor = query_executor        

    async def __all(self, query:Query):
        if self.query_executor:            
            return await self.query_executor.get_all(query=query)
        return query.all()
    
    async def __first(self, id_key, query:Query, disable_caching: bool = False):
        if not disable_caching and self.query_executor:
            return await self.query_executor.get_first(id_key=id_key, query=query)
        return query.first()


    async def get_photos(self, keyword: str | None, tag: str | None, skip: int, limit: int, user: User, db: Session) -> List[Photo]:
        """
        Retrieves a list of photos based on optional keyword search and tag filtering with pagination.

        Args:
            keyword (str | None): An optional keyword to search for in photo descriptions (case-insensitive).
            tag (str | None): An optional tag name to filter photos by.
            skip (int): The number of photos to skip in the results (for pagination).
            limit (int): The maximum number of photos to return in the results (for pagination).
            user (User): The currently authenticated user.
            db (Session): The database session object.
        Returns:
            List[Photo]: A list of Photo objects matching the search criteria and pagination parameters.
        """
        query = db.query(Photo)  
        filters = []
        if keyword:
            filters.append(func.lower(Photo.description).like(f"%{keyword.lower()}%"))
        if tag:
            filters.append(Photo.tags.any(func.lower(Tag.name) == tag.lower()))
        if filters:    
            query = query.filter(or_(False, *filters))
        query = query.offset(skip).limit(limit)
        return await self.__all(query=query)


    async def get_photo(self, photo_id:uuid.UUID, user: User, db: Session, disable_caching: bool = False) -> Photo:
        """
        Retrieves a single photo by its unique identifier.

        Args:
            photo_id (uuid.UUID): The unique identifier of the photo to retrieve.
            user (User): The currently authenticated user.
            db (Session): The database session object.
        Returns:
            Photo: A Photo object representing the retrieved photo, or None if no photo is found with the specified ID.
        """
        query = db.query(Photo).filter(Photo.id == photo_id)
        photo = await self.__first(id_key=photo_id, query=query, disable_caching=disable_caching)    
        return photo


    def __parse_filter(self, filter: str | None) -> dict:
        """
        Parses a filter string into a dictionary format.

        The expected filter string format is a comma-separated list of key-value pairs,
        where each pair is further separated by a double colon (::).

        Args:
            filter (str | None): The filter string to parse (optional).
        Returns:
            dict: A dictionary representation of the parsed filter, or an empty dictionary if the filter is None.
        """
        if filter:
            lst = filter.split("|")
            dct = {}
            for f in lst:
                key, value = f.split("::")
                dct[key] = value
            return dct
        return {}


    async def __ensure_tags(self, tags: list[str], db: Session) -> list[Tag]:
        """
        Ensures that tags associated with a photo exist in the database.

        This method iterates through the provided list of tags and checks if each tag
        already exists in the database. If a tag doesn't exist, a new Tag record is created
        and added to the database. The method returns a list of Tag objects representing
        the ensured tags.

        Args:
            tags (list[str]): A list of tag names to ensure.
            db (Session): The database session object.
        Returns:
            list[Tag]: A list of Tag objects representing the ensured tags (may contain duplicates).
        """
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
        """
        Creates a new Photo record in the database.

        This method takes a PhotoBase schema object containing photo details (description, tags, url)
        and creates a new Photo record with the provided information. The method also ensures that
        the specified tags exist in the database.

        Args:
            body (PhotoBase): A PhotoBase schema object containing photo details.
            user (User): The currently authenticated user who owns the photo.
            db (Session): The database session object.
        Returns:
            Photo: A Photo object representing the newly created photo record.
        """    
        tags = await self.__ensure_tags(tags=body.tags, db=db)
        photo = Photo(description=body.description, 
                    tags=tags, 
                    url=body.url,
                    asset_type=AssetType.origin,
                    user = user)
        db.add(photo)
        db.commit()
        db.refresh(photo)
        await CacheableQuery.trigger(photo.id, event_prefix="photo", event_name="created")
        return photo


    async def create_transformation(self, url: str, description: str, tags: list[Tag], asset_type: AssetType, user: User, db: Session) -> Photo:
        """
        Creates a new Photo record representing a transformation of an existing URL.

        This method creates a new Photo record with the provided description, tags, asset type,
        and the specified URL. It's intended to represent a transformed version of an existing
        image located at the given URL.

        Args:
            url (str): The URL of the existing image to be transformed.
            description (str): The description of the transformed photo.
            tags (list[Tag]): A list of tags associated with the transformed photo.
            asset_type (AssetType): The asset type of the transformed photo.
            user (User): The currently authenticated user who owns the photo.
            db (Session): The database session object.
        Returns:
            Photo: A Photo object representing the newly created transformed photo record.
        """    
        photo = Photo(description=description, 
                    tags=tags, 
                    url=url,
                    asset_type=asset_type,
                    user = user)
        db.add(photo)
        db.commit()
        db.refresh(photo)
        await CacheableQuery.trigger(photo.id, event_prefix="photo", event_name="created")
        return photo


    async def remove_photo(self, photo: Photo, user: User, db: Session) -> Photo | None:
        """
        Deletes a Photo record from the database.

        This method attempts to delete the provided Photo object from the database.
        If the deletion is successful, the method also invalidates any potential cache entries
        associated with the deleted photo (if a cache executor is used).

        Args:
            photo (Photo): The Photo object to be deleted.
            user (User): The currently authenticated user (for authorization checks).
            db (Session): The database session object.
        Returns:
            Photo | None: The deleted Photo object if successful, or None if the photo wasn't found.
        """        
        if photo:
            db.delete(photo)
            db.commit()
            await CacheableQuery.trigger(photo.id, event_prefix="photo", event_name="deleted")
        return photo


    async def update_photo_details(self, photo: Photo, body: PhotoUpdate, user: User, db: Session) -> Photo | None:       
        """
        Updates the details of an existing Photo record in the database.

        This method takes a Photo object and a PhotoUpdate schema object containing updated information
        (description and tags). It updates the specified photo record with the new details, ensuring that
        any new tags are created in the database. The method also invalidates any potential cache entries
        associated with the updated photo (if a cache executor is used).

        Args:
            photo (Photo): The Photo object to be updated.
            body (PhotoUpdate): A PhotoUpdate schema object containing updated details.
            user (User): The currently authenticated user (for authorization checks).
            db (Session): The database session object.
        Returns:
            Photo | None: The updated Photo object if successful, or None if the photo wasn't found.
        """
        if photo:
            tags = [tag for tag in body.tags if tag and not any(t.name == tag for t in photo.tags)]    
            logger.info(tags)
            if len(photo.tags) + len(tags) > 5:
                raise IndexError(f"Maximum number of tags per photo is 5, and this photo already has {len(photo.tags)} tags.")    
            if body.description:
                photo.description = body.description
            if tags:
                photo.tags += await self.__ensure_tags(tags=tags, db=db)
            db.add(photo)
            db.commit()
            await CacheableQuery.trigger(photo.id, event_prefix="photo", event_name="updated")
        return photo


repository_photos = PhotosRepository(query_executor=CacheableQueryExecutor(event_prefixes=["photo", "comment", "user"]))

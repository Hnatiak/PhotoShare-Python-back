import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch
from uuid import uuid4

import uuid
import logging
from pydantic_core import ValidationError
import uvicorn.logging
from typing import List
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload, Query
from src.entity.models import Photo, Tag, User, AssetType
from src.schemas.schemas import PhotoBase, PhotoUpdate
from app.src.exceptions.exceptions import AccessDeniedException
from src.repository.photos import PhotosRepository
from src.services.cache import CacheableQueryExecutor, QueryExecutor


class TestAsyncPhotosRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.mock_query = Mock(spec=Query)
        self.mock_photo = Mock(spec=Photo)
        self.mock_tag = Mock(spec=Tag)
        self.user = User(id=1)
        self.repository = PhotosRepository(query_executor=AsyncMock(spec=CacheableQueryExecutor))
        self.repository._PhotosRepository__ensure_tags = AsyncMock()
        self.repository.query_executor.invalidate_cache_for_all = AsyncMock()
        self.repository.query_executor.invalidate_cache_for_first = AsyncMock()

    async def test_get_all_photos_with_filters(self):
        keyword = "test"
        tag = "nature"
        skip = 0
        limit = 10
        filters = [
            func.lower(Photo.description).like(f"%{keyword.lower()}%"),
            Photo.tags.any(func.lower(Tag.name) == tag.lower()),
        ]

        self.mock_session.query.return_value = self.mock_query
        self.mock_query.filter.side_effect = [self.mock_query, self.mock_query]
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.repository.query_executor.get_all.return_value = [self.mock_photo]

        photos = await self.repository.get_photos(keyword, tag, skip, limit, self.user, self.mock_session)

        self.mock_session.query.assert_called_once()
        self.mock_query.filter.assert_called_once()
        self.repository.query_executor.get_all.assert_called_once()
        self.assertEqual(photos, [self.mock_photo])

    async def test_get_all_photos_no_filters(self):
        skip = 0
        limit = 10

        self.mock_session.query.return_value = self.mock_query
        self.mock_query.offset.return_value = self.mock_query
        self.mock_query.limit.return_value = self.mock_query
        self.repository.query_executor.get_all.return_value = [self.mock_photo]

        photos = await self.repository.get_photos(None, None, skip, limit, self.user, self.mock_session)

        self.mock_session.query.assert_called_once()
        self.repository.query_executor.get_all.assert_called_once()
        self.assertEqual(photos, [self.mock_photo])

    async def test_get_photo_by_id(self):
        photo_id = uuid4()
        self.repository.query_executor.get_first.return_value = self.mock_photo

        photo = await self.repository.get_photo(photo_id, self.user, self.mock_session)

        self.mock_session.query.assert_called_once()
        self.repository.query_executor.get_first.assert_called_once()
        self.assertEqual(photo, self.mock_photo)

    async def test_get_photo_by_id_not_found(self):
        photo_id = uuid4()
        self.repository.query_executor.get_first.return_value = None

        photo = await self.repository.get_photo(photo_id, self.user, self.mock_session)

        self.mock_session.query.assert_called_once()        
        self.repository.query_executor.get_first.assert_called_once()
        self.assertIsNone(photo)

    async def test_create_photo(self):
        tags = ["nature", "life"]
        tag_models = [Tag(id=1, name="nature"), Tag(id=2, name="life")]
        body = PhotoBase(description="test photo", url="https://example.com/test.jpg", tags=tags)
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None    
        self.repository._PhotosRepository__ensure_tags.return_value=tag_models

        photo = await self.repository.create_photo(body, self.user, self.mock_session)

        self.mock_session.add.assert_called_once_with(photo)
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once_with(photo)
        self.assertIsInstance(photo, Photo)
        self.assertEqual(photo.description, body.description)
        self.assertEqual(photo.url, body.url)
        self.assertEqual(photo.asset_type, AssetType.origin)
        self.assertEqual(photo.user, self.user)
        self.assertEqual(photo.tags, tag_models)
        self.repository.query_executor.invalidate_cache_for_all.assert_called_once()

    async def test_create_photo_with_existing_tags(self):
        existing_tag = Tag(id=1, name="nature")
        body = PhotoBase(description="test photo", url="https://example.com/test.jpg", tags=["nature"])
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.repository._PhotosRepository__ensure_tags.return_value=[existing_tag]
        
        photo = await self.repository.create_photo(body, self.user, self.mock_session)

        self.repository._PhotosRepository__ensure_tags.assert_called_once()
        self.mock_session.add.assert_called_once_with(photo)
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once_with(photo)
        self.assertIsInstance(photo, Photo)
        self.assertEqual(photo.tags[0], existing_tag)

    async def test_create_photo_too_many_tags(self):        
        with self.assertRaises(ValidationError):
            body = PhotoBase(description="test photo", url="https://example.com/test.jpg", tags=["nature", "beach", "landscape", "sky", "cloud", "exceed"])
            await self.repository.create_photo(body, self.user, self.mock_session)

    async def test_update_photo_details(self):
        photo_id = uuid4()
        tags = ["new_tag"]
        body = PhotoUpdate(description="updated description", tags=tags)
        self.mock_session.query.return_value = Mock(filter=Mock(return_value=Mock(first=self.mock_photo)))
        self.mock_photo.tags = set()
        self.mock_ensure_tags = AsyncMock(return_value=[Mock(spec=Tag, name="new_tag")])
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None

        await self.repository.update_photo_details(photo_id, body, self.user, self.mock_session, False)

        self.mock_session.query.assert_called_once()
        self.repository._PhotosRepository__ensure_tags.assert_called_once_with(tags=tags, db=self.mock_session)
        self.mock_photo.description = body.description
        self.mock_photo.tags.add(self.mock_ensure_tags.return_value[0])
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.has_calls(call(), call())
        self.repository.query_executor.invalidate_cache_for_all.assert_called_once()
        self.repository.query_executor.invalidate_cache_for_first.assert_called_once_with(photo_id)


    async def test_update_photo_details_with_authorization_error(self):
        photo_id = uuid4()
        body = PhotoUpdate(description="updated description", tags=[])        
        self.mock_photo.user = Mock(spec=User)
        self.mock_photo.user.id = "different_user_id"
        self.mock_session.query.return_value = Mock(filter=Mock(return_value=Mock(first=self.mock_photo)))

        with self.assertRaises(AccessDeniedException):
            await self.repository.update_photo_details(photo_id, body, self.user, self.mock_session, True)

    async def test_remove_photo(self):
        photo_id = uuid4()
        self.mock_session.delete.return_value = None
        self.mock_session.commit.return_value = None
        self.repository.query_executor.get_first.return_value = self.mock_photo

        photo = await self.repository.remove_photo(photo_id, self.user, self.mock_session, False)

        self.mock_session.query.assert_called_once()
        self.mock_session.delete.assert_called_once_with(self.mock_photo)
        self.mock_session.commit.assert_called_once()
        self.repository.query_executor.invalidate_cache_for_all.assert_called_once()
        self.repository.query_executor.invalidate_cache_for_first.assert_called_once_with(photo_id)
        self.assertIsInstance(photo, Photo)

    async def test_remove_photo_not_found(self):
        photo_id = uuid4()
        self.repository.query_executor.get_first.return_value = None

        photo = await self.repository.remove_photo(photo_id, self.user, self.mock_session, False)

        self.mock_session.query.assert_called_once()
        self.assertIsNone(photo)

    async def test_remove_photo_with_authorization_error(self):
        photo_id = uuid4()
        self.mock_session.query.return_value = Mock(filter=Mock(return_value=Mock(first=self.mock_photo)))
        self.mock_photo.user = Mock(spec=User)
        self.mock_photo.user.id = "different_user_id"

        with self.assertRaises(AccessDeniedException):
            await self.repository.remove_photo(photo_id, self.user, self.mock_session, True)


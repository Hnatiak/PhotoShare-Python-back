import unittest
import sys
import os
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from src.entity.models import Comment, User, Photo
from src.schemas.schemas import CommentNewSchema
from src.repository.comments import (create_comment, 
                                     edit_comment, 
                                     get_comments_by_user_id, 
                                     get_comments_by_photo_id, 
                                     get_comments_by_user_and_photo_ids, 
                                     delete_comment, 
                                     get_author_by_comment_id)

class TestSyncComments(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.photo_1 = uuid.uuid4()
        cls.photo_2 = uuid.uuid4()
        cls.photo_3 = uuid.uuid4()
        
        cls.new_comment = {
            'photo_id': cls.photo_1,
            'text': 'comment text'
        }
        cls.existing_comment = Comment(
            id=1,
            user_id=1,
            photo_id=cls.photo_1,
            text="old comment"
        )
        cls.admin = User(
            id=1,
            email="admin@myapp.com",
            role="admin"
        )
        cls.moderator = User(
            id=2,
            email="moderator@myapp.com",
            role="moderator"
        )
        cls.user1 = User(
            id=3,
            email="first_user@myapp.com",
            role="admin"
        )
        cls.user2 = User(
            id=4,
            email="second_user@myapp.com",
            role="admin"
        )

    # @unittest.skip('not implemented')
    def setUp(self):
        self.mocked_db_responce = MagicMock()
        self.local_session = MagicMock(spec=Session)
        self.local_session.execute.return_value= self.mocked_db_responce

    # @unittest.skip('not implemented')
    async def test_create_comment(self):
        body=CommentNewSchema(**self.new_comment)
        result = await create_comment(user=self.user1, body=body, db=self.local_session)

        self.assertEqual(self.local_session.add.call_count, 1)
        self.assertEqual(self.local_session.commit.call_count, 1)
        self.assertEqual(self.local_session.refresh.call_count, 1)
        self.assertIsInstance(result, Comment)
        self.assertEqual(result.user_id, self.user1.id)


    @unittest.skip('not implemented')
    async def test_edit_comment(self):
        # self.mocked_db_responce.unique().scalar_one_or_none.return_value = 
        result = await edit_comment(record_id=self.existing_comment.id, body=self.new_comment, db=self.local_session)

        self.assertEqual(self.local_session.execute.call_count, 1)
        self.assertEqual(
            self.moked_db_responce.unique().scalar_one_or_none.call_count, 1)
        self.assertEqual(self.local_session.commit.call_count, 1)
        self.assertEqual(self.local_session.refresh.call_count, 1)

        self.assertIsInstance(result, Comment)
        # self.assertEqual(result.id, record_id)
        # self.assertEqual(result.first_name, record_update.first_name)
        # self.assertEqual(result.last_name, record_update.last_name)
        # self.assertEqual(result.email, record_update.email)
        # self.assertEqual(result.birthday, record_update.birthday)
        # self.assertEqual(result.notes, record_update.notes)
        # self.assertNotEqual(result.updated_at, self.created_date,
        #                     msg='updated_at should change')

    @unittest.skip('not implemented')
    async def test_get_comments_by_user_id(self):
        result = await get_comments_by_user_id()

    @unittest.skip('not implemented')
    async def test_get_comments_by_photo_id(self):
        result = await get_comments_by_photo_id()

    @unittest.skip('not implemented')
    async def test_get_comments_by_user_and_photo_ids(self):
        result = await get_comments_by_user_and_photo_ids()

    @unittest.skip('not implemented')
    async def test_delete_comment(self):
        result = await delete_comment()

    @unittest.skip('not implemented')
    async def test_get_author_by_comment_id(self):
        result = await get_author_by_comment_id()

if __name__ == "__main__":
    unittest.main()
import unittest
import sys
import os
import uuid
from unittest.mock import MagicMock
from time import sleep

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from tests.mock_db import MockDB, USERS, PHOTOS
from src.entity.models import Comment, User, Photo, Role
from src.schemas.schemas import CommentNewSchema
from src.repository.comments import (create_comment, 
                                     edit_comment, 
                                     get_comments_by_user_id, 
                                     get_comments_by_photo_id, 
                                     get_comments_by_user_and_photo_ids, 
                                     delete_comment, 
                                     get_comment_by_id)

class TestSyncComments(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        Mock_db = MockDB(users=USERS, photos=PHOTOS)
        cls.local_session = Mock_db()

        cls.admin = cls.local_session.query(
            User).filter_by(role=Role.admin).first()
        cls.moderator = cls.local_session.query(
            User).filter_by(role=Role.moderator).first()
        cls.users = cls.local_session.query(
            User).filter_by(role=Role.user).all()
        cls.photos = cls.local_session.query(Photo).all()

        cls.moderator_comment_text = 'moderator comment text'
        cls.user_1_comment_text = 'user_1 comment text'
        cls.user_2_comment_text = 'user_2 comment text'
        cls.new_comment_text = 'new comment text'

    def setUp(self):
        self.mock_photo = MagicMock(id=uuid.uuid4())
        self.mock_user = User(id=1000)
        self.mock_comment = Comment(id=1000)

    # @unittest.skip('not implemented')
    # async def test_create_comment(self):
    #     body=CommentNewSchema(**self.new_comment)
    #     result = await create_comment(user=self.user1, body=body, db=self.local_session)

    #     self.assertEqual(self.local_session.add.call_count, 1)
    #     self.assertEqual(self.local_session.commit.call_count, 1)
    #     self.assertEqual(self.local_session.refresh.call_count, 1)
    #     self.assertIsInstance(result, Comment)
    #     self.assertEqual(result.user_id, self.user1.id)

    async def test_create_comment_moderator(self):
        author = self.moderator
        text = self.moderator_comment_text
        photo_id = self.photos[0].id
        body = CommentNewSchema(photo_id=photo_id, text=text)
        result = await create_comment(user=author, body=body, db=self.local_session)
        self.assertIsInstance(result, Comment)
        self.assertEqual(result.user_id, author.id)
        self.assertEqual(result.text, text)
        self.assertEqual(result.photo_id, photo_id)

    async def test_create_comment_user_1(self):
        author = self.users[0]
        text = self.user_1_comment_text
        photo_id = self.photos[0].id
        body = CommentNewSchema(photo_id=photo_id, text=text)
        result = await create_comment(user=author, body=body, db=self.local_session)
        self.assertIsInstance(result, Comment)
        self.assertEqual(result.user_id, author.id)
        self.assertEqual(result.text, text)
        self.assertEqual(result.photo_id, photo_id)

    async def test_create_comment_user_2(self):
        author = self.users[1]
        text = self.user_2_comment_text
        photo_id = self.photos[1].id
        body = CommentNewSchema(photo_id=photo_id, text=text)

        result = await create_comment(user=author, body=body, db=self.local_session)

        self.assertIsInstance(result, Comment)
        self.assertEqual(result.user_id, author.id)
        self.assertEqual(result.text, text)
        self.assertEqual(result.photo_id, photo_id)

    async def test_edit_comment_exists(self):
        records = self.local_session.query(Comment).all()
        record = records[-1]
        old_text = record.text
        new_text = self.new_comment_text
        sleep(1)

        result = await edit_comment(record_id=record.id, comment=new_text, db=self.local_session)

        self.assertIsInstance(result, Comment)
        self.assertEqual(result.id, record.id)
        self.assertEqual(result.text, new_text)
        self.assertNotEqual(result.text, old_text)
        self.assertNotEqual(result.created_at, result.updated_at)

    async def test_edit_comment_not_exists(self):
        record = self.mock_comment
        new_text = self.new_comment_text

        result = await edit_comment(record_id=record.id, comment=new_text, db=self.local_session)

        self.assertEqual(result, None)

    async def test_get_comments_by_user_id_exist(self):
        user = self.users[1]
        text = self.new_comment_text

        result = await get_comments_by_user_id(user_id=user.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], Comment)
        self.assertEqual(result[0].user_id, user.id)
        self.assertEqual(result[0].text, text)

    async def test_get_comments_by_user_id_not_exist(self):
        user = self.mock_user

        result = await get_comments_by_user_id(user_id=user.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_comments_not_exist_by_user_id(self):
        user = self.admin

        result = await get_comments_by_user_id(user_id=user.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_comments_by_photo_id_exists(self):
        photo = self.photos[0]

        result = await get_comments_by_photo_id(photo_id=photo.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], Comment)

    async def test_get_comments_not_exists_by_photo_id(self):
        photo = self.photos[2]

        result = await get_comments_by_photo_id(photo_id=photo.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_comments_by_photo_id_not_exists(self):
        photo = self.mock_photo

        result = await get_comments_by_photo_id(photo_id=photo.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_comments_by_user_and_photo_ids_exist(self):
        user = self.users[0]
        record = self.local_session.query(Comment).filter_by(user_id=user.id).first()

        result = await get_comments_by_user_and_photo_ids(user_id=user.id, photo_id=record.photo_id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], Comment)
        self.assertEqual(result[0].user_id, user.id)

    async def test_get_comments_by_user_and_photo_ids_not_exist(self):
        user = self.users[0]
        photo = self.mock_photo

        result = await get_comments_by_user_and_photo_ids(user_id=user.id, photo_id=photo.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_comments_by_user_not_exist_and_photo_ids(self):
        user = self.mock_user
        record = self.local_session.query(Comment).first()

        result = await get_comments_by_user_and_photo_ids(user_id=user.id, photo_id=record.photo_id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_comments_by_user_not_exist_and_photo_ids_not_exist(self):
        user = self.mock_user
        photo = self.mock_photo

        result = await get_comments_by_user_and_photo_ids(user_id=user.id, photo_id=photo.id, offset=0, limit=10, db=self.local_session)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    async def test_get_author_by_comment_id(self):
        user = self.users[1]
        records = self.local_session.query(Comment).filter_by(user_id=user.id).all()
        record = records[-1]
        text = record.text

        result = await get_comment_by_id(rec_id=record.id, db=self.local_session)

        self.assertIsInstance(result, Comment)
        self.assertEqual(result.user_id, user.id)
        self.assertEqual(result.text, text)

    async def test_delete_comment_exist(self):
        user = self.moderator
        record = self.local_session.query(Comment).filter_by(user_id=user.id).first()
        text = record.text
        photo_id = record.photo_id

        result = await delete_comment(record_id=record.id, db=self.local_session)

        self.assertIsInstance(result, Comment)
        self.assertEqual(result.user_id, user.id)
        self.assertEqual(result.text, text)
        self.assertEqual(result.photo_id, photo_id)

    async def test_delete_comment_not_exist(self):
        record = self.mock_comment

        result = await delete_comment(record_id=record.id, db=self.local_session)

        self.assertEqual(result, None)

if __name__ == "__main__":
    unittest.main()
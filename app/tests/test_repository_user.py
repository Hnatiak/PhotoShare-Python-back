import unittest
from unittest.mock import Mock
from datetime import date

from sqlalchemy.orm import Session

from src.entity.models import User
from src.schemas.schemas import UserSchema, UserUpdateSchema, RoleUpdateSchema
from src.repository.users import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    change_role,
    update_user,
    update_avatar,
    get_users,
)


class TestAsyncUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(
            id=1,
            username="Test Name",
            email="testemail@ukr.net",
            phone="0674444444",
            birthday=date(1975, 12, 12),
            password="123qweas",
        )
        self.user2 = User(
            id=2,
            username="Test Name2",
            email="testemail2@ukr.net",
            phone="0674444442",
            birthday=date(1975, 12, 12),
            password="123qwea2",
        )
        self.session = Mock(spec=Session)
        print("Start Test")

    async def test_get_user_by_email(self):
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = self.user
        self.session.query.return_value = query_mock
        result = await get_user_by_email(email=self.user.email, db=self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, self.user.username)
        self.assertEqual(result.email, self.user.email)

    async def test_get_users(self):
        query_mock = Mock()
        query_mock.offset.return_value.limit.return_value.all.return_value = [self.user, self.user2]
        self.session.query.return_value = query_mock
        result = await get_users(skip=0, limit=10, db=self.session)
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIsInstance(item, User)  

    async def test_get_user_by_id(self):
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = self.user
        self.session.query.return_value = query_mock
        result = await get_user_by_id(user_id=self.user.id, db=self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.id, self.user.id)

    async def test_create_user(self):
        body = UserSchema(
            username="test_name",
            email="testemail@ukr.net",
            password="123qweas",
        )
        result = await create_user(body, self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)

    async def test_change_role(self):
        user = User()
        body = RoleUpdateSchema(
            role="moderator"
        )
        mocked_user = Mock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await change_role(user_id=self.id, body=body, db=self.session)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.role, body.role)

    async def test_update_user(self):
        user = User()
        body = UserUpdateSchema(
            username="test_name",
            phone="0674444444",
            birthday=date(1975, 12, 12),
        )
        mocked_user = Mock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await update_user(user_id=self.id, body=body, db=self.session)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)

    async def test_update_avatar(self):
        url = "https://www.gravatar.com/avatar/64cd6c93150a4ead4d329f7f949715fc"
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = self.user
        self.session.query.return_value = query_mock
        result = await update_avatar(email=self.user.email, url=url, db=self.session)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.avatar, url)

    def tearDown(self):
        print("End Test")


if __name__ == "__main__":
    unittest.main()

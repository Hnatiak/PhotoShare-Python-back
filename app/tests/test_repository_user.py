import unittest
from unittest.mock import MagicMock, AsyncMock

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schemas.schemas import UserSchema, UserResponse, UserUpdateSchema, RoleUpdateSchema
from src.repository.users import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    change_role,
    update_user,
    update_avatar,
    get_users,
)


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user = User(
            id=1,
            name="Test Name",
            email="testemail@ukr.net",
            phone="0674444444",
            birthday=date(1975, 12, 12),
            password="123qweas",
        )
        # self.contact = Contact(id=1, email="testemail@ukr.net")
        self.session = AsyncMock(spec=AsyncSession)
        print("Start Test")

    async def test_get_user_by_email(self):
        user = User()
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await get_user_by_email(email=self.user.email, db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_id(self):
        user = User()
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await get_user_by_id(email=self.user.id, db=self.session)
        self.assertEqual(result, user)

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
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await change_role(uyser_id=self.id, body=body, db=self.session)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.role, body.role)

    async def test_update_contact(self):
        user = User()
        body = UserUpdateSchema(
            username="test_name",
            phone="0674444444",
            birthday=date(1975, 12, 12),
        )
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await update_user(uyser_id=self.id, body=body, db=self.session)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)

    async def test_update_avatar(self):
        user = User()
        url = "https://www.gravatar.com/avatar/64cd6c93150a4ead4d329f7f949715fc"
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mocked_user
        result = await update_avatar(email=self.user.email, url=url, db=self.session)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.avatar, url)

    async def test_get_users(self):
        users = [User(), User(), User()]
        mocked_user = MagicMock()
        mocked_user.scalars.return_value.all.return_value = users
        self.session.execute.return_value = mocked_user
        result = await get_users(offset=0, limit=10, db=self.session)
        self.assertEqual(result, users)


    def tearDown(self):
        print("End Test")


if __name__ == "__main__":
    unittest.main()

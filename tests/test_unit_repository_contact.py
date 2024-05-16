import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import date
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema
from src.repository.contacts import create_contact, get_contacts, get_all_contacts, get_contact, search_contacts, update_contact, delete_contact

class TestAsyncContact(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user = User(id=1, username='test_user', password='test123534423w', confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_all_contacts(self):
        limit = 10
        offset = 0
        contacts = [Contact(id=1, first_name='test_firstname_1', last_name='test_lastname_1', email='test_user_1@gmail.com', phone_number='+380979797665', birthday='13.05.1996', additional_data=True, user=self.user)] # , created_at='test', updated_at='test',
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_all_contacts(limit, offset, self.session)
        self.assertEqual(result, contacts)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [Contact(id=1, first_name='test_firstname_1', last_name='test_lastname_1', email='test_user_1@gmail.com', phone_number='+380979797665', birthday='13.05.1996', additional_data=True, user=self.user)] # , created_at='test', updated_at='test',
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_create_contact(self):
        body = ContactSchema(
            first_name='test_firstname',
            last_name='test_lastname',
            email='test_user@gmail.com',
            phone_number='+380979797665',
            birthday=date(1996, 5, 13),
            additional_data=True
        )
        result = await create_contact(body, self.session, self.user)
        self.assertEqual(result.first_name, 'test_firstname')
        self.assertEqual(result.last_name, 'test_lastname')
        self.assertEqual(result.email, 'test_user@gmail.com')
        self.assertEqual(result.phone_number, '+380979797665')
        self.assertEqual(result.birthday, date(1996, 5, 13))
        self.assertTrue(result.additional_data)

    async def test_update_contact(self):
        body = ContactUpdateSchema(
            first_name='test_firstname',
            last_name='test_lastname',
            email='test_user@gmail.com',
            phone_number='+380979797665',
            birthday=date(1996, 5, 13),
            additional_data=True
        )
        mocked_todo = MagicMock()
        mocked_todo.scalar_one_or_none.return_value = Contact(
            id=1,
            first_name='User_title',
            last_name='User_description',
            user=self.user
        )
        self.session.execute.return_value = mocked_todo
        result = await update_contact(1, body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, 'test_firstname')
        self.assertEqual(result.last_name, 'test_lastname')
        self.assertEqual(result.email, 'test_user@gmail.com')
        self.assertEqual(result.phone_number, '+380979797665')
        self.assertEqual(result.birthday, date(1996, 5, 13))
        self.assertTrue(result.additional_data)

    async def test_delete_contact(self):
        mocked_todo = MagicMock()
        mocked_todo.scalar_one_or_none.return_value = Contact(
            id=1,
            first_name='User_title',
            last_name='User_description',
            user=self.user
        )
        self.session.execute.return_value = mocked_todo
        result = await delete_contact(1, self.session, self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()

        self.assertIsInstance(result, Contact)
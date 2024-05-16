from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema
from sqlalchemy import or_, func
from datetime import datetime, timedelta

async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    """
    The get_contacts function returns a list of contacts from the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Skip a certain number of contacts
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the database
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()

async def get_all_contacts(limit: int, offset: int, db: AsyncSession):
    """
    The get_all_contacts function returns a list of contacts from the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Skip a certain number of contacts
    :param db: AsyncSession: Pass the database session to the repository
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    stmt = select(Contact).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()

async def get_contact(contact_id: int, db: AsyncSession, user: User):
    """
    The get_contact function returns a contact from the database.

    :param contact_id: int: Get the contact by id
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the database
    :return: A contact object
    :doc-Author: Kolobok
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()

async def search_contacts(query: str, db: AsyncSession, user: User):
    """
    The search_contacts function searches for contacts in the database.

    :param query: str: Search for contacts by name, email, or phone number
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the database
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    stmt = select(Contact).filter(
        or_(
            Contact.first_name.ilike(f'%{query}%'),
            Contact.last_name.ilike(f'%{query}%'),
            Contact.email.ilike(f'%{query}%')
        )
    ).filter(Contact.user_id == user.id)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()

async def get_contacts_upcoming_birthdays(days: int, db: AsyncSession, user: User):
    """
    The get_contacts_upcoming_birthdays function returns a list of contacts that have upcoming birthdays.

    :param days: int: Specify the number of days in the future
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the database
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    stmt = select(Contact).filter(
        Contact.birthday.between(today, end_date),
        Contact.user_id == user.id
    )
    contacts = await db.execute(stmt)
    return contacts.scalars().all()

async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactSchema: Get the data from the request body
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the database
    :return: A contact object
    :doc-Author: Kolobok
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user) # (title=body.title)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User):
    """
    The update_contact function updates a contact in the database.

    :param contact_id: int: Get the contact id from the url
    :param body: ContactUpdateSchema: Get the data from the request body
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the database
    :return: A contact object
    :doc-Author: Kolobok
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone_number = body.phone_number
        contact.birthday = body.birthday
        contact.additional_data = body.additional_data
        await db.commit()
        await db.refresh(contact)
    return contact

async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Get the contact id from the url
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the database
    :return: A contact object
    :doc-Author: Kolobok
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact
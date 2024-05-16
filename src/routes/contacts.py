from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User, Role
from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactSchema, ContactUpdateSchema, ContactResponse
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(prefix='/contacts', tags=['contacts'])

access_to_route_all = RoleAccess([Role.admin, Role.moderator])

@router.get('/', response_model=list[ContactResponse])
async def get_contacts(limit: int = Query(default=10, ge=10, le=500), offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts function returns a list of contacts from the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Skip a certain number of contacts
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)
    return contacts

@router.get('/all', response_model=list[ContactResponse], dependencies=[Depends(access_to_route_all)])
async def get_all_contacts(limit: int = Query(default=10, ge=10, le=500), offset: int = Query(default=0, ge=0), db: AsyncSession = Depends(get_db)):
    """
    The get_all_contacts function returns a list of contacts from the database.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Skip a certain number of contacts
    :param db: AsyncSession: Pass the database session to the repository
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    contacts = await repositories_contacts.get_all_contacts(limit, offset, db)
    return contacts

@router.get('/{contact_id}', response_model=ContactResponse)
async def get_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The get_contact function returns a contact from the database.

    :param contact_id: int: Get the contact by id
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A contact object
    :doc-Author: Kolobok
    """
    contact = await repositories_contacts.get_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ти намагаєшся знайти взагалі щось, чого не існує")
    return contact

@router.post('/', response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactSchema: Get the data from the request body
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A contact object
    :doc-Author: Kolobok
    """
    contact = await repositories_contacts.create_contact(body, db, user)
    return contact

@router.put('/{contact_id}')
async def update_contact(body: ContactUpdateSchema, contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The update_contact function updates a contact in the database.

    :param body: ContactUpdateSchema: Get the data from the request body
    :param contact_id: int: Get the contact id from the path
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A contact object
    :doc-Author: Kolobok
    """
    contact = await repositories_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ти намагаєшся корегувати взагалі щось, чого не існує")
    return contact

@router.delete('/{contact_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Get the contact id from the path
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A response object
    :doc-Author: Kolobok
    """
    contact = await repositories_contacts.delete_contact(contact_id, db, user)
    return contact

@router.get('/search/', response_model=list[ContactResponse])
async def search_contacts(query: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The search_contacts function searches for contacts in the database.

    :param query: str: Search for contacts in the database
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    contacts = await repositories_contacts.search_contacts(query, db, user)
    return contacts

@router.get('/upcoming-birthdays/', response_model=list[ContactResponse])
async def get_upcoming_birthdays(days: int = Query(default=7, ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The get_upcoming_birthdays function returns a list of contacts that have upcoming birthdays.

    :param days: int: Specify the number of days in the future
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-Author: Kolobok
    """
    contacts = await repositories_contacts.get_contacts_upcoming_birthdays(days, db, user)
    return contacts
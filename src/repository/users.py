from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    The get_user_by_email function takes an email address and a database session

    :param email: str: Specify the type of the email parameter
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user

async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    The create_user function creates a new user in the database.

    :param body: UserSchema: Specify the type of the body parameter
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the refresh token in the database.

    :param user: User: Specify the user that is being updated
    :param token: str | None: Pass the refresh token to the function
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object
    """
    user.refresh_token = token
    await db.commit()

async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    The confirmed_email function takes an email address and a database session
    and sets the confirmed field of the user with that email address to True.

    :param email: str: Specify the email address of the user
    :param db: AsyncSession: Pass the database session to the function
    :return: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()
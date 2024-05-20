from libgravatar import Gravatar
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from src.entity.models import User
from src.schemas.schemas import UserModel, UserUpdateSchema, RoleUpdateSchema
import redis.asyncio as redis
from sqlalchemy.future import select

from src.schemas.user import UserResponse

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from src.conf.config import settings
from src.entity.models import BlacklistToken
from time import time
from asyncio import sleep



async def get_user_by_email(email: str, db: Session) -> User:
    return db.query(User).filter(User.email == email).first()


async def get_user_by_id(user_id: int, db: Session) -> User:
    return db.query(User).filter(User.id == user_id).first()


async def create_user(body: UserModel, db: Session) -> User:
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def chandge_role(user_id: int, body: RoleUpdateSchema, db: Session):
    stmt = select(User).filter_by(id=user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        return None
    user.role = body.role
    db.commit()
    db.refresh(user)
    return user


async def update_user(user_id: int, body: UserUpdateSchema, db: Session):
    stmt = select(User).filter_by(id=user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        return None
    user.username = body.username
    # user.phone = body.phone
    # user.birthday = body.birthday
    db.commit()
    db.refresh(user)
    return user


async def update_avatar(email: str, url: str, db: AsyncSession):
    contact = await get_user_by_email(email, db)
    contact.avatar = url
    db.commit()
    db.refresh(contact)
    return contact


async def confirmed_email(email: str, db: Session) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_token(user: User, token: str | None, db: Session) -> None:
    user.refresh_token = token
    db.commit()


# async def update_avatar(email, url: str, db: Session) -> User:
#     user = await get_user_by_email(email, db)
#     user.avatar = url
#     db.commit()
#     return user

# async def edit_my_profile(avatar: UploadFile, new_username: str, user: User, db: AsyncSession):
#     if new_username:
#         user.username = new_username
#     if avatar:
#         avatar_path = update_avatar(user.email, url=await avatar.read(), db=db)
#         user.avatar_url = avatar_path
#     db.add(user)
#     await db.commit()
#     await db.refresh(user)
#     return user



BLACKLISTED_TOKENS = "blacklisted_tokens"

r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    encoding="utf-8",
    decode_responses=True,
)


async def add_to_blacklist(token: str, db: Session) -> None:
    blacklist_token = BlacklistToken(token=token, blacklisted_on=datetime.now())
    db.add(blacklist_token)
    db.commit()
    db.refresh(blacklist_token)


async def is_token_blacklisted(token: str) -> bool:
    return await r.sismember(BLACKLISTED_TOKENS, token)


async def get_users(skip: int, limit: int, db: Session) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

async def dell_from_bleck_list(expired, token: str, db: AsyncSession) -> None:
    bl_token = db.query(BlacklistToken).filter(BlacklistToken.token == token).first()
    time_now = time()
    time_for_sleep = expired - time_now
    await sleep(time_for_sleep)
    db.delete(bl_token)
    db.commit()


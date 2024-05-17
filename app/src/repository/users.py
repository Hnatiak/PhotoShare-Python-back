from libgravatar import Gravatar
from sqlalchemy.orm import Session
from typing import List

from src.entity.models import User
# from src.schemas.schemas import UserModel
from src.schemas.schemas import UserModel
# import aioredis
import redis.asyncio as redis
from sqlalchemy.future import select

from src.schemas.user import UserResponse

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from src.conf.config import settings

async def get_user_by_email(email: str, db: Session) -> User:
    return db.query(User).filter(User.email == email).first()

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

async def confirmed_email(email: str, db: Session) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()

async def update_token(user: User, token: str | None, db: Session) -> None:
    user.refresh_token = token
    db.commit()

async def update_avatar(email, url: str, db: Session) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user




async def edit_my_profile(avatar: UploadFile, new_username: str, user: User, db: AsyncSession):
    if new_username:
        user.username = new_username
    if avatar:
        avatar_path = save_avatar(avatar)
        user.avatar_url = avatar_path
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

def save_avatar(avatar: UploadFile) -> str:
    pass

BLACKLISTED_TOKENS = "blacklisted_tokens"

r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, encoding="utf-8", decode_responses=True)

# async def add_to_blacklist(token: str, expire: int = None, db: AsyncSession = None) -> None:
#     await r.sadd(BLACKLISTED_TOKENS, token)
#     if expire:
#         await r.expire(token, expire)

async def add_to_blacklist(token: str) -> None:
    # Ensure token is a string
    if not isinstance(token, str):
        raise ValueError("Token should be a string")
    await r.set(token, "blacklisted")


async def is_token_blacklisted(token: str) -> bool:
    return await r.sismember(BLACKLISTED_TOKENS, token)


async def get_all_users(db: AsyncSession) -> List[UserResponse]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.from_orm(user) for user in users]
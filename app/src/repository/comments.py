from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from datetime import datetime

from src.database.models import Comment, User
from src.schemas import CommentNewSchema, CommentResponseSchema

async def create_comment(user: User, body: CommentNewSchema, db: Session) -> CommentResponseSchema:
    comment = Comment(**body.model_dump())
    comment.user_id = user.id
    db.add(comment)
    # await db.commit()
    db.commit()
    # comment = await db.refresh(comment)
    db.refresh(comment)
    return comment

# TODO - see routes
# async def edit_comment(user: User, record_id: int, body: CommentNewSchema, db: Session):
#     stmt = select(Comment).filter_by(id=record_id, photo_id=body.photo_id)
#     # result = await db.execute(stmt)
#     result = db.execute(stmt)
#     result = result.scalar_one_or_none()
#     if result:
#         result.text = body.text
#         # await db.commit()
#         # await db.refresh(result)
#         db.commit()
#         db.refresh(result)
#     return result


async def get_comments_by_user_id(user_id: int, offset: int, limit: int, db: Session):
    stmt = select(Comment).filter_by(user_id=user_id).offset(offset).limit(limit)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    return result.scalars().all()

async def get_comments_by_photo_id(photo_id: int, offset: int, limit: int, db: Session):
    stmt = select(Comment).filter_by(photo_id=photo_id).offset(offset).limit(limit)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    return result.scalars().all()

async def get_comments_by_user_and_photo_ids(user_id: int, photo_id: int, offset: int, limit: int, db: Session):
    stmt = select(Comment).filter_by(user_id=user_id, photo_id=photo_id).offset(offset).limit(limit)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    return result.scalars().all()

async def delete_comment():
    pass


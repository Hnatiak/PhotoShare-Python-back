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
    await db.commit()
    comment = await db.refresh(comment)
    return comment

async def edit_comment():
    pass

async def get_comments_by_user_id():
    pass

async def get_comments_by_photo_id():
    pass

async def delete_comment():
    pass


import uuid
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, text, func
# from datetime import datetime

from src.entity.models import Comment, User, Photo
from src.schemas.schemas import CommentNewSchema


async def create_comment(user: User, body: CommentNewSchema, db: Session) -> Comment | None:
    '''
    Creates new comment.

    Args:    
        user: Author of comment.
        body: data of new comment record
        db: sync db session
    Returns:
        obj: 'Comment' | None: Comment with ID or None.
    '''
    comment = Comment(**body.model_dump())
    comment.user_id = user.id
    db.add(comment)
    # await db.commit()
    db.commit()
    # comment = await db.refresh(comment)
    db.refresh(comment)
    return comment


async def edit_comment(record_id: int, body: CommentNewSchema, db: Session) -> Comment | None:
    '''
    Updates specific comment by ID.

    Args:    
        record_id: ID of record to change
        body: updated data of the comment record
        db: sync db session
    Returns:
        obj: 'Comment' | None: Comment with ID or None.
    '''
    stmt = select(Comment).filter_by(id=record_id, photo_id=body.photo_id)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    result = result.unique().scalar_one_or_none()
    if result:
        result.text = body.text
        # result.updated_at = func.now() # has defaut value in Model
        # await db.commit()
        # await db.refresh(result)
        db.commit()
        db.refresh(result)
    return result


async def get_comments_by_user_id(user_id: int, offset: int, limit: int, db: Session) -> list[Comment]:
    '''
    Retrieves comments by ID of a specific author.
    
    Args:
        user_id: The ID of author of comments to retrieve.
        offset: The number of contacts to skip.
        limit: The maximum number of contacts to return.
        db: sync db session
    Returns:
        obj: 'list' of obj: Comment: A list of comments.
    '''
    stmt = select(Comment).filter_by(
        user_id=user_id).offset(offset).limit(limit)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    return result.unique().scalars().all()


async def get_comments_by_photo_id(photo_id: uuid.UUID, offset: int, limit: int, db: Session) -> list[Comment]:
    '''
    Retrieves comments by ID of a specific photo.
    
    Args:
        photo_id: The ID of photo to retrieve comments.
        offset: The number of contacts to skip.
        limit: The maximum number of contacts to return.
        db: sync db session
    Returns:
        obj: 'list' of obj: Comment: A list of comments.
    '''
    stmt = select(Comment).filter_by(
        photo_id=photo_id).offset(offset).limit(limit)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    return result.unique().scalars().all()


async def get_comments_by_user_and_photo_ids(user_id: int, photo_id: uuid.UUID, offset: int, limit: int, db: Session) -> list[Comment]:
    '''
    Retrieves comments by ID of a specific author and ID of a specific photo.
    
    Args:
        user_id: The ID of author of comments to retrieve.
        photo_id: The ID of photo to retrieve comments.
        offset: The number of contacts to skip.
        limit: The maximum number of contacts to return.
        db: sync db session
    Returns:
        obj: 'list' of obj: Comment: A list of comments.
    '''
    stmt = select(Comment).filter_by(user_id=user_id,
                                     photo_id=photo_id).offset(offset).limit(limit)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    return result.unique().scalars().all()


async def delete_comment(record_id: int, db: Session) -> None:
    '''
    Deletes comment by ID.

    Args:    
        record_id: ID of record to delete
        db: sync db session
    Returns:
        None
    '''
    stmt = select(Comment).filter_by(id=record_id)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    result = result.unique().scalar_one_or_none()
    if result:
        # await db.delete(result)
        # await db.commit()
        db.delete(result)
        db.commit()

    return result


async def get_author_by_comment_id(rec_id: int, db: Session) -> User | None:
    '''
    Retrieves comment author by record ID.
    
    Args:
        rec_id: The ID of comment record.
        db: sync db session
    Returns:
        obj: 'User': Author of comments.
    '''
    stmt = select(Comment).filter_by(id=rec_id)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    # result = result.scalar_one_or_none()
    result = result.unique().scalar_one_or_none()
    if result:
        result = result.user

    return result

import uuid
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, text, func
# from datetime import datetime

from src.entity.models import Comment, User, Photo
from src.schemas.schemas import CommentNewSchema
from src.services.cache import CacheableQuery


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
    await CacheableQuery.trigger(comment.photo_id, event_prefix="comment", event_name="created")
    return comment


async def edit_comment(record_id: int, comment: str, db: Session) -> Comment | None:
    '''
    Updates specific comment by ID.

    Args:    
        record_id: ID of record to change
        comment: updated comment text
        db: sync db session
    Returns:
        obj: 'Comment' | None: Comment with ID or None.
    '''
    stmt = select(Comment).filter_by(id=record_id)
    # result = await db.execute(stmt)
    result = db.execute(stmt)
    result = result.unique().scalar_one_or_none()
    if result:
        result.text = comment
        # result.updated_at = func.now() # has defaut value in Model
        # await db.commit()
        # await db.refresh(result)
        db.commit()
        db.refresh(result)
        await CacheableQuery.trigger(result.photo_id, event_prefix="comment", event_name="updated")
    return result


# async def update_comment(record: Comment, comment: str, db: Session) -> Comment | None:
#     '''
#     Updates specific comment by ID.

#     Args:    
#         record_id: ID of record to change
#         body: updated data of the comment record
#         db: sync db session
#     Returns:
#         obj: 'Comment' | None: Comment with ID or None.
#     '''
#     record.text = comment
#     # result.updated_at = func.now() # has defaut value in Model
#     # await db.commit()
#     # await db.refresh(result)
#     db.commit(record)
#     result = db.refresh(record)
#     return result

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


async def delete_comment(record_id: int, db: Session) -> Comment|None:
    '''
    Deletes comment by ID.

    Args:    
        record_id: ID of record to delete
        db: sync db session
    Returns:
        obj: Comment | None: Record, that was deleted
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
        await CacheableQuery.trigger(result.photo_id, event_prefix="comment", event_name="deleted")
    return result


# async def get_author_by_comment_id(rec_id: int, db: Session) -> User|None:
#     '''
#     Retrieves comment author by record ID.
    
#     Args:
#         rec_id: The ID of comment record.
#         db: sync db session
#     Returns:
#         obj: 'User': Author of comments.
#     '''
#     stmt = select(Comment).filter_by(id=rec_id)
#     # result = await db.execute(stmt)
#     result = db.execute(stmt)
#     # result = result.scalar_one_or_none()
#     result = result.unique().scalar_one_or_none()
#     if result:
#         result = result.user

#     return result


async def get_comment_by_id(rec_id: int, db: Session) -> Comment|None:
    '''
    Retrieves comment by record ID.
    
    Args:
        rec_id: The ID of comment record.
        db: sync db session
    Returns:
        obj: 'Comment' | None: Comment.
    '''
    stmt = select(Comment).filter_by(id=rec_id)
    # result = await db.execute(stmt)
    result = db.execute(stmt)

    result = result.unique().scalar_one_or_none()

    return result
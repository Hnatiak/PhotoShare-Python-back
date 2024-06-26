import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, Body
# from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.services.auth import auth_service
from src.services.roles import admin_access, moderator_access, is_owner
from src.schemas.schemas import CommentNewSchema, CommentResponseSchema
from src.entity.models import User, Comment
from src.repository import comments as rep_comments
from src.repository.photos import repository_photos
from src.exceptions.exceptions import RETURN_MSG


router = APIRouter(prefix='/comments', tags=["comments"])


@router.post("/{photo_id}", response_model=CommentResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(comment: str = Body(min_length=1, max_length=500, description="Comment text", 
                                             title='Comment', examples=["user comment"]),
                         photo_id: uuid.UUID = Path(description="ID of photo to comment"),
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)) -> Comment | None:
    '''
    Creates new comment.

    Args:    
        comment: text of new comment
        photo_id: ID of the photo
        current_user: The user to retrieve ontacts for.
        db: sync db session Default=Depends(get_db)
    Returns:
        obj: 'Comment' | None: Comment with ID or None.
    '''

    photo = await repository_photos.get_photo(photo_id=photo_id, user=current_user, db=db, disable_caching=True)
    # photo = await repository_photos.get_photo(photo_id=photo_id, user=current_user, db=db)
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=RETURN_MSG.record_not_found)

    body = CommentNewSchema(photo_id=photo_id, text=comment)
    result = await rep_comments.create_comment(user=current_user, body=body, db=db)
    return result


@router.put("/record/{comment_id}", response_model=CommentResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def edit_comment(comment: str = Body(min_length=1, max_length=500, description="Comment text", title='Comment', examples=["user comment"]),
                       comment_id: int = Path(description="ID of comment to change"),
                       db: Session = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)) -> Comment | None:
    '''
    Updates specific comment.

    Args:    
        comment: text of new comment
        comment_id: ID of record to change
        current_user: current user.
        db: sync db session Default=Depends(get_db)
    Returns:
        obj: 'Comment' | None: Comment with ID or None.
    '''
    
    record = await rep_comments.get_comment_by_id(rec_id=comment_id, db=db)
    # author = await rep_comments.get_author_by_comment_id(rec_id=comment_id, db=db)
    
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=RETURN_MSG.record_not_found)

    current_user_is_owner = await is_owner(current_user=current_user, item_owner_id=record.user_id)
    if (current_user.role not in moderator_access.allowed_roles) and not current_user_is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=RETURN_MSG.access_forbiden)

    result = await rep_comments.edit_comment(record_id=comment_id, comment=comment, db=db)

    return result

# TODO display of comments should be restricted to registered users only?
@router.get("/{photo_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_photo_id(photo_id: uuid.UUID = Path(description="ID of photo to find comments"),
                                   offset: int = Query(default=0, ge=0, description="Records to skip in response"),
                                   limit: int = Query(default=10, ge=1, le=50, description="Records per response to show"),
                                   db: Session = Depends(get_db),
                                   current_user: User = Depends(auth_service.get_current_user)) -> list[Comment]:
    '''
    Retrieves a list of comments for a specific photo with specified pagination parameters.
    
    Args:
        photo_id: ID of the photo
        current_user: current user.
        limit: The maximum number of comments to return.
        offset: The number of comments to skip.
        db: sync db session
    Returns:
        obj: 'list' of obj: Comment: A list of comments.
    '''
    result = await rep_comments.get_comments_by_photo_id(photo_id=photo_id, offset=offset, limit=limit, db=db)
    return result

# TODO display of comments should be restricted to registered users only?
@router.get("/users/", response_model=list[CommentResponseSchema])
async def get_comments_by_user_id(user_id: int = Query(description="ID of author of comments"),
                                  offset: int = Query(default=0, ge=0, description="Records to skip in response"),
                                  limit: int = Query(default=10, ge=1, le=50, description="Records per response to show"),
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(auth_service.get_current_user)) -> list[Comment]:
    '''
    Retrieves a list of comments of a specific author with specified pagination parameters.
    
    Args:
        user_id: Author of comments ID
        current_user: current user.
        limit: The maximum number of comments to return.
        offset: The number of comments to skip.
        db: sync db session
    Returns:
        obj: 'list' of obj: Comment: A list of comments.
    '''
    result = await rep_comments.get_comments_by_user_id(user_id=user_id, offset=offset, limit=limit, db=db)
    return result

# TODO display of comments should be restricted to registered users only?
@router.get("/users/{user_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_user_and_photo_id(user_id: int = Path(description="ID of author of comments"),
                                            photo_id: uuid.UUID = Query(description="ID of photo to find comments"),
                                            offset: int = Query(default=0, ge=0, description="Records to skip in response"),
                                            limit: int = Query(default=10, ge=1, le=50, description="Records per response to show"),
                                            db: Session = Depends(get_db),
                                            current_user: User = Depends(auth_service.get_current_user)) -> list[Comment]:
    '''
    Retrieves a list of comments for a specific photo from specific author with specified pagination parameters.
    
    Args:
        user_id: Author of comments ID
        photo_id: ID of the photo
        limit: The maximum number of comments to return.
        offset: The number of comments to skip.
        db: sync db session
        current_user: current user.
    Returns:
        obj: 'list' of obj: Comment: A list of comments.
    '''
    result = await rep_comments.get_comments_by_user_and_photo_ids(user_id=user_id, photo_id=photo_id, offset=offset, limit=limit, db=db)
    return result

@router.delete("/record/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(moderator_access)])
async def delete_comment(comment_id: int = Path(description="ID of comment to delete"),
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)) -> None:
    '''
    Deletes specific comment.

    Args:    
        comment_id: ID of record to delete
        current_user: The user to retrieve ontacts for.
        db: async db session Default=Depends(get_db)
    Returns:
        None
    '''

    result = await rep_comments.delete_comment(record_id=comment_id, db=db)
    return result

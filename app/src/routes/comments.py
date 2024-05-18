from fastapi import APIRouter, HTTPException, Depends, status,Path, Query
# from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.services.auth import auth_service
from src.schemas.schemas import CommentNewSchema, CommentResponseSchema
from src.entity.models import User, Comment
from src.repository import comments as rep_comments


router = APIRouter(prefix='/comments', tags=["comments"])

@router.post("/", response_model=CommentResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(body: CommentNewSchema, 
                         db: Session = Depends(get_db), 
                         current_user: User = Depends(auth_service.get_current_user)) -> Comment|None:
    '''
    Creates new comment.

    Args:    
        body: data of new comment record
        current_user: The user to retrieve ontacts for.
        db: sync db session Default=Depends(get_db)
    Returns:
        obj: 'Comment' | None: Comment with ID or None.
    '''
    result = await rep_comments.create_comment(user=current_user, body=body, db=db)
    return result

# TODO limit access to comment owner, moderator or admin
@router.put("/{rec_id}",response_model=CommentResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def edit_comment(body: CommentNewSchema, 
                       rec_id: int = Path(description="ID of record to change"), 
                       db: Session = Depends(get_db), 
                       current_user: User = Depends(auth_service.get_current_user)) -> Comment|None:
    '''
    Updates specific comment.

    Args:    
        body: updated data of the comment record
        rec_id: ID of record to change
        current_user: current user.
        db: sync db session Default=Depends(get_db)
    Returns:
        obj: 'Comment' | None: Comment with ID or None.
    '''

    result = await rep_comments.edit_comment(record_id=rec_id, body=body, db=db)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record ID or photo ID not found")
    return result

# TODO display of comments should be restricted to registered users only?
@router.get("/user_id={user_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_user_id(user_id: int, 
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
@router.get("/photo_id={photo_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_photo_id(photo_id: int,
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
@router.get("/user_id={user_id}/photo_id={photo_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_user_and_photo_id(user_id: int, 
                                            photo_id: int,
                                            offset: int = Query(default=0, ge=0, description="Records to skip in response"),
                                            limit: int = Query(default=10, ge=1, le=50, description="Records per response to show"),
                                            db: Session = Depends(get_db), 
                                            current_user: User = Depends(auth_service.get_current_user)) -> list[Comment]:
    '''
    Retrieves a list of comments for a specific photo from specific author with specified pagination parameters.
    
    Args:
        user_id: Author of comments ID
        photo_id: ID of the photo
        current_user: current user.
        limit: The maximum number of comments to return.
        offset: The number of comments to skip.
        db: sync db session
    Returns:
        obj: 'list' of obj: Comment: A list of comments.
    '''
    result = await rep_comments.get_comments_by_user_and_photo_ids(user_id=user_id, photo_id=photo_id, offset=offset, limit=limit, db=db)
    return result

# TODO limit access to moderator and admin
@router.delete("/{rec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(rec_id: int = Path(description="ID of record to delete"),
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)) -> None:
    '''
    Deletes specific comment.

    Args:    
        rec_id: ID of record to delete
        current_user: The user to retrieve ontacts for.
        db: async db session Default=Depends(get_db)
    Returns:
        None
    '''
    
    result = await rep_comments.delete_comment(record_id=rec_id, db=db)
    return result

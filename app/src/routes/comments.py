from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request, Path, Query
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.services.auth import auth_service
from src.schemas.schemas import CommentNewSchema, CommentResponseSchema
from src.entity.models import User
from src.repository import comments as rep_comments


router = APIRouter(prefix='/comments', tags=["comments"])

@router.post("/", response_model=CommentResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(body: CommentNewSchema, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    result = await rep_comments.create_comment(user=current_user, body=body, db=db)
    return result

# TODO limit access to comment owner or moderator
# @router.put("/{rec_id}",response_model=CommentResponseSchema, status_code=status.HTTP_202_ACCEPTED)
# async def edit_comment(body: CommentNewSchema, 
#                        rec_id: int = Path(description="ID of record to change"), 
#                        db: Session = Depends(get_db), 
#                        current_user: User = Depends(auth_service.get_current_user)):

#     result = await rep_comments.edit_comment(user=current_user, record_id=rec_id, body=body, db=db)
#     if not result:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record ID or photo ID not found")
#     return result

# TODO display of comments should be restricted to registered users only?
@router.get("/user_id={user_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_user_id(user_id: int, 
                               offset: int = Query(default=0, ge=0, description="Records to skip in response"),
                               limit: int = Query(default=10, ge=1, le=50, description="Records per response to show"),
                               db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    result = await rep_comments.get_comments_by_user_id(user_id=user_id, offset=offset, limit=limit, db=db)
    return result

# TODO display of comments should be restricted to registered users only?
@router.get("/photo_id={photo_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_photo_id(photo_id: int,
                                   offset: int = Query(default=0, ge=0, description="Records to skip in response"),
                                   limit: int = Query(default=10, ge=1, le=50, description="Records per response to show"),
                                   db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    result = await rep_comments.get_comments_by_photo_id(photo_id=photo_id, offset=offset, limit=limit, db=db)
    return result

# TODO display of comments should be restricted to registered users only?
@router.get("/user_id={user_id}/photo_id={photo_id}", response_model=list[CommentResponseSchema])
async def get_comments_by_photo_id(user_id: int, 
                                   photo_id: int,
                                   offset: int = Query(default=0, ge=0, description="Records to skip in response"),
                                   limit: int = Query(default=10, ge=1, le=50, description="Records per response to show"),
                                   db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    result = await rep_comments.get_comments_by_user_and_photo_ids(user_id=user_id, photo_id=photo_id, offset=offset, limit=limit, db=db)
    return result

async def delete_comment():
    pass

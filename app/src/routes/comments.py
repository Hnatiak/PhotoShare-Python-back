from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.services.auth import auth_service
from src.schemas import CommentNewSchema, CommentResponseSchema
from src.database.models import User
from src.repository import comments as rep_comments


router = APIRouter(prefix='/comments', tags=["comments"])

@router.post("/", response_model=CommentResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(body: CommentNewSchema, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    result = await rep_comments.create_comment(user=current_user, body=body, db=db)
    return result


async def edit_comment():
    pass


async def get_comments_by_user_id():
    pass


async def get_comments_by_photo_id():
    pass


async def delete_comment():
    pass

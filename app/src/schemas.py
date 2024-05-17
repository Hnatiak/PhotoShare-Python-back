from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, PastDate
from pydantic_extra_types.phone_numbers import PhoneNumber
    

class UserModel(BaseModel):
    username: str = Field(min_length=2, max_length=16)
    email: str
    password: str = Field(min_length=4, max_length=10)


class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr

class CommentResponseSchema(BaseModel):
    id: int
    user_id: int
    photo_id: int
    text: str
    created_at: datetime
    updated_at: datetime


class CommentNewSchema(BaseModel):
    photo_id: int
    text: str

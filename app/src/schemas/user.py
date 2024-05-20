from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from datetime import datetime
from src.entity.models import Role


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    # last_name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=10, max_length=50)

# class UserSchema(BaseModel):
#     username: str = Field(min_length=3, max_length=50)
#     # last_name: str = Field(min_length=3, max_length=50)
#     email: EmailStr
#     phone: str = Field(min_length=10, max_length=13)
#     birthday: date
#     password: str = Field(min_length=10, max_length=50)

# class UserDb(BaseModel):
#     id: int
#     username: str
#     email: str
#     phone: str
#     birthday: date
#     created_at: datetime
#     avatar: str
#     role: Role
#     class Config:
#         from_attributes = True

class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr
    avatar: str
    role: Role
    isLoggedIn: bool

    class Config:
        from_attributes = True


# class UserResponse(BaseModel):
#     user: UserDb
#     detail: str = "User successfully created"

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RequestEmail(BaseModel):
    email: EmailStr

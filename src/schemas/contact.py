
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date, datetime

from src.schemas.user import UserResponse


class ContactSchema(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: Optional[bool] = False

class ContactUpdateSchema(ContactSchema):
    additional_data: bool

class ContactResponse(BaseModel):
    id: int = 1
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: bool
    created_at: datetime | None
    updated_at: datetime | None
    user: UserResponse | None

    model_config = ConfigDict(from_attributes = True)  # noqa
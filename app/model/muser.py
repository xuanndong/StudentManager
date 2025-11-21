from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    STUDENT = 'STUDENT'
    TEACHER = 'TEACHER'
    CVHT = 'CVHT'
    ADMIN = 'ADMIN'


class UserBase(BaseModel):
    mssv: str
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None  # Số điện thoại
    role: UserRole = UserRole.STUDENT
    is_active: bool = True
    administrative_class_id: str | None = None  # Lớp chính quy (chỉ cho STUDENT)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class UserLogin(BaseModel):
    mssv: str
    password: str


class UserResponse(UserBase):
    id: str = Field(..., alias='_id')

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "mssv": "20201234",
                    "email": "abc@gmail.com",
                    "full_name": "John Washion",
                    "role": "STUDENT",
                    "is_active": True,
                    "administrative_class_id": None
                }
            ]
        }
    }

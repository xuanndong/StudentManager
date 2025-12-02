from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class PostType(str, Enum):
    ADMINISTRATIVE = "ADMINISTRATIVE"  # Bài đăng lớp chính quy (CVHT)
    COURSE = "COURSE"  # Bài đăng lớp học phần (Teacher)


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, examples=["Bài viết này rất hữu ích"])

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    user_id: str
    user_name: str | None = None  # Populated from users collection
    created_at: datetime


class PostBase(BaseModel):
    content: str = Field(..., min_length=1, examples=["Thông báo nộp bài tập lớn"])


class PostCreate(PostBase):
    pass 

class PostUpdate(BaseModel):
    content: str

class PostResponse(PostBase):
    id: str = Field(..., alias="_id")
    post_type: PostType
    class_id: str  # ID của AdministrativeClass hoặc CourseClass
    author_id: str
    author_name: str | None = None
    author_role: str | None = None
    likes: list[str] = []
    comments: list[CommentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

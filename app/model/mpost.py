from pydantic import BaseModel, Field
from datetime import datetime

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, examples=["Bài viết này rất hữu ích"])

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    user_id: str
    created_at: datetime


class PostBase(BaseModel):
    content: str = Field(..., min_length=1, examples=["Thông báo nộp bài tập lớn"])


class PostCreate(PostBase):
    pass 

class PostUpdate(BaseModel):
    content: str

class PostResponse(PostBase):
    id: str = Field(..., alias="_id")
    class_id: str
    author_id: str
    likes: list[str] = [] # Danh sách user likes
    comments: list[CommentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "class_id": "",
                    "author_id": "",
                    "likes": [],
                    "comments": [],
                    "created_at": "",
                    "updated_at": ""
                }
            ]
        }
    }
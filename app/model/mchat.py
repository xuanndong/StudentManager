from pydantic import BaseModel, Field
from datetime import datetime

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: str = Field(..., alias="_id")
    conversation_id: str
    sender_id: str
    content: str
    created_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "conversation_id": "",
                    "sender_id": "",
                    "content": "",
                    "created_at": ""
                }
            ]
        }
    }


class LastMessage(BaseModel):
    content: str
    sender_id: str
    created_at: datetime


class ConversationCreate(BaseModel):
    receiver_id: str # Người mình muốn nhắn tới

class ConversationResponse(BaseModel):
    id: str = Field(..., alias="_id")
    participants: list[str] # Danh sách user_id tham gia
    last_message: LastMessage | None = None
    updated_at: datetime

    other_user_name: str | None = None  # Tên người chat
    other_user_phone: str | None = None  # Phone người chat

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "participants": [],
                    "last_message": "",
                    "updated_at": "",
                    "other_user_name": "Nguyen Van A",
                    "other_user_phone": "0912345678"
                }
            ]
        }
    }

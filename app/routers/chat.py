from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

from app.model.mchat import ConversationCreate, ConversationResponse, MessageResponse, MessageCreate
from app.dependencies import get_current_user
from app.core.socket import manager # Import socket manager

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1"), tags=['Chat System'])

# --- REST API (Quản lý hội thoại & Lịch sử) ---

# Tạo cuộc hội thoại mới (hoặc lấy cái cũ nếu đã có)
@router.get("/search-by-phone/{phone}")
async def search_user_by_phone(
    phone: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Tìm user theo số điện thoại"""
    db: AsyncDatabase = request.app.state.db
    
    user = await db.users.find_one({"phone": phone})
    if not user:
        raise HTTPException(status_code=404, detail=f"User with phone {phone} not found")
    
    user["_id"] = str(user["_id"])
    if "password" in user:
        del user["password"]
    
    return user


@router.post("/conversations/by-phone", response_model=ConversationResponse)
async def create_conversation_by_phone(
    phone: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Tạo conversation theo số điện thoại"""
    db: AsyncDatabase = request.app.state.db
    sender_id = str(current_user["_id"])
    
    # Tìm user theo phone
    receiver = await db.users.find_one({"phone": phone})
    if not receiver:
        raise HTTPException(status_code=404, detail=f"User with phone {phone} not found")
    
    receiver_id = str(receiver["_id"])
    
    # Không thể chat với chính mình
    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")
    
    # Kiểm tra xem đã có cuộc hội thoại giữa 2 người chưa
    existing_conv = await db.conversations.find_one({
        "participants": {"$all": [sender_id, receiver_id]}
    })

    if existing_conv:
        existing_conv["_id"] = str(existing_conv["_id"])
        return existing_conv

    # Nếu chưa có -> Tạo mới
    new_conv = {
        "participants": [sender_id, receiver_id],
        "last_message": None,
        "updated_at": datetime.now()
    }
    result = await db.conversations.insert_one(new_conv)
    
    created_conv = await db.conversations.find_one({"_id": result.inserted_id})
    created_conv["_id"] = str(created_conv["_id"])
    return created_conv


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conv_in: ConversationCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    sender_id = str(current_user["_id"])
    receiver_id = conv_in.receiver_id

    # Không thể chat với chính mình
    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")

    # Kiểm tra xem receiver có tồn tại không
    if not ObjectId.is_valid(receiver_id):
        raise HTTPException(status_code=400, detail="Invalid receiver ID format")
    
    receiver = await db.users.find_one({"_id": ObjectId(receiver_id)})
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Kiểm tra xem đã có cuộc hội thoại giữa 2 người chưa
    # Tìm document nào mà participants chứa cả 2 ID
    existing_conv = await db.conversations.find_one({
        "participants": {"$all": [sender_id, receiver_id]}
    })

    if existing_conv:
        existing_conv["_id"] = str(existing_conv["_id"])
        return existing_conv

    # Nếu chưa có -> Tạo mới
    new_conv = {
        "participants": [sender_id, receiver_id],
        "last_message": None,
        "updated_at": datetime.now()
    }
    result = await db.conversations.insert_one(new_conv)
    
    created_conv = await db.conversations.find_one({"_id": result.inserted_id})
    created_conv["_id"] = str(created_conv["_id"])
    return created_conv


# Lấy danh sách hội thoại của tôi (Inbox)
@router.get("/conversations", response_model=list[ConversationResponse])
async def get_my_conversations(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])

    # Tìm tất cả hội thoại mà tôi là thành viên
    cursor = db.conversations.find({"participants": user_id}).sort("updated_at", -1)
    conversations = await cursor.to_list(length=100)

    for c in conversations:
        c["_id"] = str(c["_id"])
        
        # Populate other user info
        participants = c.get("participants", [])
        other_user_id = next((p for p in participants if p != user_id), None)
        
        if other_user_id and ObjectId.is_valid(other_user_id):
            other_user = await db.users.find_one({"_id": ObjectId(other_user_id)})
            if other_user:
                c["other_user_name"] = other_user.get("full_name", "Unknown")
                c["other_user_phone"] = other_user.get("phone", "")
    
    return conversations


# Lấy lịch sử tin nhắn của 1 hội thoại
@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])

    # Kiểm tra quyền xem (phải là thành viên)
    conv = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conv or user_id not in conv["participants"]:
         raise HTTPException(status_code=403, detail="Access denied")

    # Lấy tin nhắn
    cursor = db.messages.find({"conversation_id": conversation_id}).sort("created_at", 1)
    messages = await cursor.to_list(length=500)
    
    for m in messages:
        m["_id"] = str(m["_id"])
        
    return messages


# --- WEBSOCKET (Real-time Messaging) ---

# Connect vào: ws://localhost:8080/api/v1/ws/{user_id}
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # Chấp nhận kết nối
    await manager.connect(websocket, user_id)
    db: AsyncDatabase = websocket.app.state.db
    
    try:
        while True:
            data = await websocket.receive_json()
            
            conversation_id = data.get("conversation_id")
            content = data.get("content")
            
            if conversation_id and content:
                # Lưu tin nhắn vào DB
                msg_doc = {
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "content": content,
                    "created_at": datetime.now()
                }
                new_msg = await db.messages.insert_one(msg_doc)
                
                # Update "Last Message" cho Conversation
                await db.conversations.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {
                        "$set": {
                            "last_message": {
                                "content": content,
                                "sender_id": user_id,
                                "created_at": datetime.now()
                            },
                            "updated_at": datetime.now()
                        }
                    }
                )
                
                conv = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
                if conv:
                    participants = conv["participants"]
                    
                    # Chuẩn bị payload để gửi
                    response_msg = {
                        "event": "new_message",
                        "data": {
                            "id": str(new_msg.inserted_id),
                            "conversation_id": conversation_id,
                            "sender_id": user_id,
                            "content": content,
                            "created_at": str(datetime.now())
                        }
                    }

                    # Gửi cho tất cả thành viên (bao gồm cả chính mình để update UI)
                    for p_id in participants:
                        await manager.send_personal_message(response_msg, p_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"User {user_id} disconnected from Chat")



@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_detail(
    conversation_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID")
        
    conv = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        
    # Check xem user có trong cuộc hội thoại không
    if user_id not in conv["participants"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    conv["_id"] = str(conv["_id"])
    return conv

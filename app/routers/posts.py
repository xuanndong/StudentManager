from fastapi import APIRouter, Depends, HTTPException, status, Request
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

from app.model.mpost import PostCreate, PostResponse, CommentCreate
from app.dependencies import get_current_user

# Load .env file
load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR","/api/v1") + "/posts", tags=['Forum'])

# Kiểm tra quyền truy cập lớp
async def check_class_menbership(db: AsyncDatabase, class_id: str, user_id: str):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class id format")
    
    class_obj = await db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    if user_id != class_obj["advisor_id"] and user_id not in class_obj["student_ids"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied. You are not a menber of this class"
        )
    
    return class_obj


@router.post('/classes/{class_id}/posts', response_model=PostResponse)
async def create_post(
    class_id: str,
    post_in: PostCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> PostResponse:
    db: AsyncDatabase = request.app.state.db
    user_id = None
    if current_user['role'] == "CVHT":
        user_id = str(current_user["_id"])
    else:
        user_id = str(current_user['mssv'])

    await check_class_menbership(db, class_id, user_id)

    post_dict = post_in.model_dump()
    post_dict.update({
        "class_id": class_id,
        "author_id": user_id,
        "likes": [],
        "comments": [],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })

    new_post = await db.posts.insert_one(post_dict)
    created_post = await db.posts.find_one({"_id": new_post.inserted_id})
    created_post["_id"] = str(created_post['_id'])

    return created_post

    
# Lấy Newsfeed (Danh sách bài viết của lớp)
@router.get("/classes/{class_id}/posts", response_model=list[PostResponse])
async def get_class_posts(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    user_id = None
    if current_user['role'] == "CVHT":
        user_id = str(current_user["_id"])
    else:
        user_id = str(current_user['mssv'])

    await check_class_menbership(db, class_id, user_id)

    
    # Lấy bài viết, sắp xếp mới nhất lên đầu (-1)
    posts = await db.posts.find({"class_id": class_id}).sort("created_at", -1).to_list(length=100) # Giới hạn 100 bài gần nhất
    
    for p in posts:
        p["_id"] = str(p["_id"])
        
    return posts


# Like / Unlike bài viết
@router.put("/{post_id}/like")
async def toggle_like(
    post_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Post ID")

    # Tìm bài viết để lấy class_id check quyền
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        
    # Check xem user có thuộc lớp chứa bài viết này không
    user_id = None
    if current_user['role'] == "CVHT":
        user_id = str(current_user["_id"])
    else:
        user_id = str(current_user['mssv'])

    await check_class_menbership(db, post["class_id"], user_id)

    # Logic Toggle Like
    if user_id in post["likes"]:
        # Nếu đã like -> Bỏ like ($pull)
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"likes": user_id}}
        )
        return {"message": "Unliked", "is_liked": False}
    else:
        # Nếu chưa like -> Thêm like ($addToSet)
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$addToSet": {"likes": user_id}}
        )
        return {"message": "Liked", "is_liked": True}



# Bình luận (Comment)
@router.post("/{post_id}/comments", response_model=PostResponse)
async def add_comment(
    post_id: str,
    comment_in: CommentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Post ID")
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    user_id = None
    if current_user['role'] == "CVHT":
        user_id = str(current_user["_id"])
    else:
        user_id = str(current_user['mssv'])

    await check_class_menbership(db, post["class_id"], user_id)

    # Tạo object comment
    new_comment = {
        "user_id": user_id,
        "content": comment_in.content,
        "created_at": datetime.now()
    }

    # Push vào mảng comments trong document Post
    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$push": {"comments": new_comment}}
    )

    # Trả về post đã cập nhật để Frontend render lại ngay lập tức
    updated_post = await db.posts.find_one({"_id": ObjectId(post_id)})
    updated_post["_id"] = str(updated_post["_id"])
    
    return updated_post

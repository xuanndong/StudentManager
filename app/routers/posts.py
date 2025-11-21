from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

from app.model.mpost import PostCreate, PostResponse, CommentCreate, PostUpdate, PostType
from app.dependencies import get_current_user

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR","/api/v1") + "/posts", tags=['Forum'])


async def populate_post_user_info(db: AsyncDatabase, post: dict):
    """Populate user info vào post"""
    # Get author info
    author_id = post.get('author_id')
    
    if author_id:
        try:
            # Ensure author_id is ObjectId
            if not isinstance(author_id, ObjectId):
                author_id = ObjectId(author_id)
            
            author = await db.users.find_one({"_id": author_id})
            
            if author:
                post['author_name'] = author.get('full_name', 'Unknown')
                post['author_role'] = author.get('role', '')
            else:
                print(f"WARNING Backend: User not found for author_id={author_id}")
                post['author_name'] = 'Unknown User'
                post['author_role'] = ''
        except Exception as e:
            print(f"ERROR Backend: Error populating author: {e}")
            import traceback
            traceback.print_exc()
            post['author_name'] = 'Unknown User'
            post['author_role'] = ''
    
    # Get commenter info
    for comment in post.get('comments', []):
        commenter_id = comment.get('user_id')
        if commenter_id:
            try:
                if not isinstance(commenter_id, ObjectId):
                    commenter_id = ObjectId(commenter_id)
                
                user = await db.users.find_one({"_id": commenter_id})
                if user:
                    comment['user_name'] = user.get('full_name', 'Unknown')
            except Exception as e:
                print(f"Error populating commenter: {e}")
                comment['user_name'] = 'Unknown'
    
    return post


async def check_administrative_class_membership(db: AsyncDatabase, class_id: str, user_id: str):
    """Kiểm tra quyền truy cập lớp chính quy"""
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    class_obj = await db.administrative_classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    if user_id != class_obj["advisor_id"] and user_id not in class_obj["student_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return class_obj


async def check_course_class_membership(db: AsyncDatabase, class_id: str, user_id: str):
    """Kiểm tra quyền truy cập lớp học phần"""
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    class_obj = await db.course_classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    if user_id != class_obj["teacher_id"] and user_id not in class_obj["student_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return class_obj


# ============ ADMINISTRATIVE CLASS POSTS (CVHT) ============

@router.post('/administrative-classes/{class_id}/posts', response_model=PostResponse)
async def create_administrative_post(
    class_id: str,
    post_in: PostCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Tạo bài đăng trong lớp chính quy (CVHT hoặc sinh viên)"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    
    await check_administrative_class_membership(db, class_id, user_id)

    post_dict = post_in.model_dump()
    post_dict.update({
        "post_type": PostType.ADMINISTRATIVE,
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


@router.get("/administrative-classes/{class_id}/posts", response_model=list[PostResponse])
async def get_administrative_class_posts(
    class_id: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Lấy bài đăng của lớp chính quy"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    
    await check_administrative_class_membership(db, class_id, user_id)
    
    posts = await db.posts.find({
        "class_id": class_id,
        "post_type": PostType.ADMINISTRATIVE
    }).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    for p in posts:
        p["_id"] = str(p["_id"])
        await populate_post_user_info(db, p)
        
    return posts


# ============ COURSE CLASS POSTS (TEACHER) ============

@router.post('/course-classes/{class_id}/posts', response_model=PostResponse)
async def create_course_post(
    class_id: str,
    post_in: PostCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Tạo bài đăng trong lớp học phần (Giáo viên hoặc sinh viên)"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    
    await check_course_class_membership(db, class_id, user_id)

    post_dict = post_in.model_dump()
    post_dict.update({
        "post_type": PostType.COURSE,
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


@router.get("/course-classes/{class_id}/posts", response_model=list[PostResponse])
async def get_course_class_posts(
    class_id: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Lấy bài đăng của lớp học phần"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    
    await check_course_class_membership(db, class_id, user_id)
    
    posts = await db.posts.find({
        "class_id": class_id,
        "post_type": PostType.COURSE
    }).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    for p in posts:
        p["_id"] = str(p["_id"])
        await populate_post_user_info(db, p)
        
    return posts


# ============ COMMON POST OPERATIONS ============

@router.put("/{post_id}/like")
async def toggle_like(
    post_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Like/Unlike bài viết"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Post ID")

    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        
    user_id = str(current_user["_id"])
    
    # Check membership based on post type
    if post["post_type"] == PostType.ADMINISTRATIVE:
        await check_administrative_class_membership(db, post['class_id'], user_id)
    else:
        await check_course_class_membership(db, post['class_id'], user_id)

    if user_id in post["likes"]:
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"likes": user_id}}
        )
        return {"message": "Unliked", "is_liked": False}
    else:
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$addToSet": {"likes": user_id}}
        )
        return {"message": "Liked", "is_liked": True}


@router.post("/{post_id}/comments", response_model=PostResponse)
async def add_comment(
    post_id: str,
    comment_in: CommentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Thêm comment vào bài viết"""
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Post ID")
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    user_id = str(current_user["_id"])
    
    # Check membership
    if post["post_type"] == PostType.ADMINISTRATIVE:
        await check_administrative_class_membership(db, post['class_id'], user_id)
    else:
        await check_course_class_membership(db, post['class_id'], user_id)

    new_comment = {
        "user_id": user_id,
        "content": comment_in.content,
        "created_at": datetime.now()
    }

    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$push": {"comments": new_comment}}
    )

    updated_post = await db.posts.find_one({"_id": ObjectId(post_id)})
    updated_post["_id"] = str(updated_post["_id"])
    
    return updated_post


@router.get('/{post_id}', response_model=PostResponse)
async def get_post_detail(
    post_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Xem chi tiết bài viết"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Post ID")

    post = await db.posts.find_one({'_id': ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    user_id = str(current_user["_id"])
    
    # Check membership
    if post["post_type"] == PostType.ADMINISTRATIVE:
        await check_administrative_class_membership(db, post['class_id'], user_id)
    else:
        await check_course_class_membership(db, post['class_id'], user_id)

    post['_id'] = str(post['_id'])
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_in: PostUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Sửa bài viết (chỉ tác giả)"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid post ID")

    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        
    if post["author_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own posts")

    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {
            "$set": {
                "content": post_in.content,
                "updated_at": datetime.now()
            }
        }
    )
    
    updated_post = await db.posts.find_one({"_id": ObjectId(post_id)})
    updated_post["_id"] = str(updated_post["_id"])
    return updated_post


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Xóa bài viết (tác giả, CVHT/Teacher của lớp, hoặc Admin)"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    role = current_user.get("role")
    
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Post ID")

    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    is_author = post["author_id"] == user_id
    is_admin = role == "ADMIN"
    is_class_manager = False
    
    # Check if user is class manager
    if post["post_type"] == PostType.ADMINISTRATIVE:
        class_obj = await db.administrative_classes.find_one({"_id": ObjectId(post["class_id"])})
        is_class_manager = class_obj and class_obj["advisor_id"] == user_id
    else:
        class_obj = await db.course_classes.find_one({"_id": ObjectId(post["class_id"])})
        is_class_manager = class_obj and class_obj["teacher_id"] == user_id

    if not (is_author or is_class_manager or is_admin):
        raise HTTPException(status_code=403, detail="Permission denied")

    await db.posts.delete_one({"_id": ObjectId(post_id)})
    return {"message": "Post deleted"}

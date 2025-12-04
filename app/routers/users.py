from fastapi import APIRouter, Depends, Request, status, HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
from pydantic import BaseModel, EmailStr
from typing import Optional
from dotenv import load_dotenv
import os
import bcrypt

from app.model.muser import UserResponse
from app.dependencies import get_current_user, get_current_admin

# Load .env file
load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR","/api/v1") + "/users", tags=['Users'])


# Pydantic model for creating user
class UserCreate(BaseModel):
    mssv: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str  # STUDENT, TEACHER, CVHT, ADMIN
    password: Optional[str] = None  # If None, use default
    administrative_class_id: Optional[str] = None  # For STUDENT only


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: dict = Depends(get_current_admin)
):
    """ADMIN tạo user mới"""
    db: AsyncDatabase = request.app.state.db
    
    # Validate role
    valid_roles = ["STUDENT", "TEACHER", "CVHT", "ADMIN"]
    if user_data.role.upper() not in valid_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # Check MSSV unique
    existing_mssv = await db.users.find_one({"mssv": user_data.mssv})
    if existing_mssv:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MSSV already exists")
    
    # Check email unique
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
    
    # Hash password
    password = user_data.password if user_data.password else f"{user_data.mssv}@123"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user document
    new_user = {
        "mssv": user_data.mssv,
        "full_name": user_data.full_name,
        "email": user_data.email,
        "phone": user_data.phone,
        "role": user_data.role.upper(),
        "password": hashed_password,
        "is_active": True
    }
    
    # Insert user first
    result = await db.users.insert_one(new_user)
    user_id = str(result.inserted_id)
    new_user["_id"] = user_id
    
    # Add to administrative class if provided and role is STUDENT
    if user_data.role.upper() == "STUDENT" and user_data.administrative_class_id:
        if ObjectId.is_valid(user_data.administrative_class_id):
            # Verify class exists
            class_obj = await db.administrative_classes.find_one({"_id": ObjectId(user_data.administrative_class_id)})
            if class_obj:
                # Update user with class_id
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"administrative_class_id": user_data.administrative_class_id}}
                )
                # Add student to class
                await db.administrative_classes.update_one(
                    {"_id": ObjectId(user_data.administrative_class_id)},
                    {"$addToSet": {"student_ids": user_id}}
                )
                new_user["administrative_class_id"] = user_data.administrative_class_id
    
    # Return user without password
    if "password" in new_user:
        del new_user["password"]
    
    return new_user


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    current_user['_id'] = str(current_user["_id"])
    if "password" in current_user:
        del current_user["password"]
    return current_user


@router.get('/', response_model=list[UserResponse])
async def get_all_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    role: str | None = None, # Filter theo role
    current_user: dict = Depends(get_current_admin)
):
    db: AsyncDatabase = request.app.state.db
    query = {}
    if role:
        query["role"] = role.upper()
    
    users = await db.users.find(query).skip(skip).limit(limit).to_list(length=limit)

    for u in users:
        u['_id'] = str(u['_id'])
        if "password" in u:
            del u["password"]

    return users

 
@router.get('/{user_id}', response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_admin)
):
    db: AsyncDatabase = request.app.state.db

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user['_id'] = str(user['_id'])
    if "password" in user:
        del user["password"]

    return user


@router.put('/{user_id}', response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: dict,
    request: Request,
    current_user: dict = Depends(get_current_admin)
):
    db: AsyncDatabase = request.app.state.db
    if "_id" in user_data: del user_data["_id"]
    if "mssv" in user_data: del user_data["mssv"]

    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    updated_user = await db.users.find_one({'_id': ObjectId(user_id)})
    updated_user['_id'] = str(updated_user['_id'])
    if "password" in updated_user:
        del updated_user["password"]
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_admin)
):
    db: AsyncDatabase = request.app.state.db
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"message": f"User {user_id} has been deleted"}


@router.get('/search-by-phone/{phone}', response_model=UserResponse)
async def search_user_by_phone(
    phone: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Tìm user theo số điện thoại"""
    db: AsyncDatabase = request.app.state.db
    
    user = await db.users.find_one({"phone": phone})
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user['_id'] = str(user['_id'])
    if "password" in user:
        del user["password"]
    
    return user

from fastapi import APIRouter, Depends, Request, status, HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
from dotenv import load_dotenv
import os

from app.model.muser import UserResponse
from app.dependencies import get_current_user, get_current_admin

# Load .env file
load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR","/api/v1") + "/users", tags=['Users'])


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    current_user['_id'] = str(current_user["_id"])
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

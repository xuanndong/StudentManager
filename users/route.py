from fastapi import APIRouter, HTTPException,status, Depends
from pymongo.asynchronous.database import AsyncDatabase

from database.connection import get_db
from auth.power import get_current_user, get_current_admin_user
from database.schemas import UserRequest, UserResponse
from database.service import UserServie


users = APIRouter(prefix="/v1/users", tags=["Users API"])

@users.post("/")
async def create_new_user(user: UserRequest, db: AsyncDatabase = Depends(get_db)) -> UserResponse:
    user_service = UserServie(db)

    current = user_service.get_user_by_username(user.username)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is existed"
        )
    
    new_user = user_service.create_user(user)

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create new user failure"
        )
    
    return new_user

@users.get("/")
async def get_users_offset(
    page: int = 1,
    limit: int = 20,
    db: AsyncDatabase = Depends(get_db),
    admin: UserResponse = Depends(get_current_admin_user)
):
    if admin:
        user_service = UserServie(db)
        list_users, total_pages, total_users = user_service.get_user_admin(page, limit)

        return {
            "users": list_users,
            "pagination": {
                "total_users": total_users,
                "total_pages": total_pages,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None
            } 
        }
    

@users.get("/{userID}")
async def user_infor(
    userID: str,
    db: AsyncDatabase = Depends(get_db),
    user_data: UserResponse = Depends(get_current_user)
):
    if user_data:
        user_service = UserServie(db)
        user = user_service.get_user(userID)

        return user
    

@users.put("/{userID}")
async def update_user(
    userID: str,
    db: AsyncDatabase = Depends(get_db),
    user_data: UserResponse = Depends(get_current_user)
):
    user_service = UserServie(db)
    status_update = user_service.update_user_infor(userID, user_data)

    if not status_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failure"
        )
    
    return {
        "success": True,
        "detail": "Update successful"
    }
    

@users.delete("/{userID}")
async def delete_user(
    userID: str,
    db: AsyncDatabase = Depends(get_db),
    user_root: UserResponse = Depends(get_current_admin_user)
) -> dict:
    if not user_root:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Require admin authentication"
        )
    
    user_service = UserServie(db)
    status_delete = user_service.delete_user(userID)

    if not status_delete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delete failure"
        )
    
    return {
        "success": True,
        "detail": "Delete successful"
    }

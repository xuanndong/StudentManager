from fastapi import APIRouter, HTTPException, Request, status, Response, Cookie, Header
from pymongo.asynchronous.database import AsyncDatabase
from dotenv import load_dotenv
import os

from app.core.security import hash_password, verify_password, jwt_service
from app.model.muser import UserCreate, UserResponse, UserLogin
from app.model.token import Token


# Load .env file
load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR","/api/v1") + "/auth", tags=['Authentication'])

@router.post("/register", response_model=UserResponse)
async def register(request: Request, user: UserCreate) -> UserResponse:
    db: AsyncDatabase = request.app.state.db

    # Check email
    if await db.users.find_one({'mssv': user.mssv}):
        raise HTTPException(status_code=400, detail="Mssv already registered")
    
    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user_dict["password"])

    new_user = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": new_user.inserted_id})

    # Convert ObjectId to string
    created_user["_id"] = str(created_user["_id"])

    return created_user



@router.post("/login", response_model=Token)
async def login(request: Request, response: Response, user_login: UserLogin) -> Token:
    db: AsyncDatabase = request.app.state.db

    user = await db.users.find_one({"mssv": user_login.mssv})

    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong student code or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = jwt_service.create_access_token({
        "sub": user["mssv"],
        "role": user.get("role", "STUDENT")
    })
    refresh_token = jwt_service.create_refresh_token({
        "sub": user["mssv"],
        "role": user.get("role", "STUDENT")
    })

    # set vào Cookie
    response.set_cookie(
        key="refresh_token", # Tên cookie
        value=refresh_token, # Gía trị
        httponly=True, # JS không thể truy cập
        max_age=7 * 24 * 60 * 60,
        expires=7 * 24 * 60 * 60,
        samesite="lax", # Chống CSRF cơ bản
        secure=False # Để true nếu chạy HTTPS
    )


    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: Request, response: Response, refresh_token: str | None = Cookie(default=None)): # Tự lấy từ cookie
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    
    # Verify token
    payload = jwt_service.verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    mssv = payload.get("sub")

    # Check user
    db: AsyncDatabase = request.app.state.db
    user = await db.users.find_one({"mssv": mssv})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    # Cap lai cap token
    new_access_token = jwt_service.create_access_token({
        "sub": user["mssv"],
        "role": user.get("role", "STUDENT")
    })
    new_refresh_token = jwt_service.create_refresh_token({
        "sub": user["mssv"],
        "role": user.get("role", "STUDENT")
    })

    # Set lai cookie moi
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax",
        secure=False,
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }



@router.post("/logout")
async def logout(response: Response):
    # Xóa cookie bằng cách set nó hết hạn ngay lập tức
    response.delete_cookie("refresh_token")
    return {"message": "Logout successful"}
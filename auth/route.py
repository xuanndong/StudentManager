# Standard Libraries

# Local Modules
from database.connection import get_db
from utils.security import password_service
from utils.token import jwt_service
from auth.schemas import AccessToken
from database.schemas import UserRequest, UserResponse
from database.service import UserServie
from auth.power import get_current_user

# Third-party Libraries
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.asynchronous.database import AsyncDatabase


auth = APIRouter(prefix="/v1/auth", tags=["Authentication"])

@auth.post("/login")
async def login(response: Response, data: OAuth2PasswordRequestForm = Depends(), db: AsyncDatabase = Depends(get_db)) -> AccessToken:
    user_service = UserServie(db)
    user = await user_service.get_user_by_username(data.username)

    if not user or not password_service.verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="username or password not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = {"user_id": str(user["_id"]), "role": user["role"]}

    access_token = jwt_service.create_access_token(data=payload)
    refresh_token = jwt_service.create_refresh_token(data=payload)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/v1/auth"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@auth.post("/register")
async def register(data: UserRequest, db: AsyncDatabase = Depends(get_db)):
    user_service = UserServie(db)
    existing_user = await user_service.get_user_by_username(data.username)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username is exist"
        )
    
    hashed_password = password_service.get_password_hash(data.password)

    new_user_data = data.model_dump()
    new_user_data["password"] = hashed_password

    new_user = await user_service.create_user(data)

    return new_user


@auth.post("/refresh")
async def refresh(refresh_token: str | None = Cookie(default=None)) -> AccessToken:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not found refresh token"
        )
    
    new_access_token = jwt_service.refresh_access_token(refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expiration"
        )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@auth.get("/me")
async def me(user_current: UserResponse = Depends(get_current_user)):
    return user_current

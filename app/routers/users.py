from fastapi import APIRouter, Depends
from dotenv import load_dotenv
import os

from app.model.muser import UserResponse
from app.dependencies import get_current_user

# Load .env file
load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR","/api/v1") + "/users", tags=['Users'])


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user



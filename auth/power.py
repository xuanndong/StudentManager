# Standard Libraries

# Local Modules
from database.connection import get_db
from utils.token import jwt_service
from database.service import UserServie
from database.schemas import UserResponse

# Third-party Libraries
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.asynchronous.database import AsyncDatabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncDatabase = Depends(get_db)
):
    token_data = jwt_service.verify_token(token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token khong hop le"
        )
    
    user_service = UserServie(db)
    current_user_doc = await user_service.get_user(token_data["user_id"])

    if not current_user_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    return current_user_doc


async def get_current_admin_user(
    current_user: UserResponse = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error authorization"
        )
    
    return current_user


async def get_current_student_user(
    current_user: UserResponse = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error authorization"
        )
    
    return current_user


async def get_current_teacher_user(
    current_user: UserResponse = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error authorization"
        )
    
    return current_user

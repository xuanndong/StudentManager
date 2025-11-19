from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.model.muser import UserResponse
from pymongo.asynchronous.database import AsyncDatabase

from app.core.security import jwt_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW_Authenticate": "Bearer"}
    )

    try:
        payload = jwt_service.verify_token(token)
        mssv: str = payload.get("sub")

        if mssv is None:
            raise credentials_exception
    except Exception as e:
        raise credentials_exception
    
    db: AsyncDatabase = request.app.state.db
    user = await db.users.find_one({"mssv": mssv})
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_cvht(current_user: dict = Depends(get_current_user)):
    role = current_user.get('role')
    if role != "CVHT":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have permission to perform this action"
        )
    
    return current_user
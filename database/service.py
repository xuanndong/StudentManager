from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId

from database.schemas import UserRequest, UserResponse
from utils.security import password_service

class UserServie:
    def __init__(self, db: AsyncDatabase):
        self.collection = db.users


    async def create_user(self, user: UserRequest) -> UserResponse:
        hashed_password = password_service.get_password_hash(user.password)

        user["password"] = hashed_password

        insert_result = await self.collection.insert_one(user)
        user["id"] = str(insert_result.inserted_id)

        return UserResponse.model_validate(user)
    

    async def get_user(self, user_id: str) -> UserResponse | None:
        query = {"_id": ObjectId(user_id)}

        result = await self.collection.find_one(query)

        if result:
            result["id"] = str(result["_id"])
            return UserResponse.model_validate(result)
        
        return None


    async def get_user_by_username(self, username: str) -> UserResponse | None:
        query = {"username": username}

        result = await self.collection.find_one(query)

        if result:
            result["id"] = str(result["_id"])
            return UserResponse.model_validate(result)
        
        return None


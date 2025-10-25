from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId

from database.schemas import UserRequest, UserResponse, UserUpdate
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
    

    async def get_user_admin(self, page: int, limit: int):
        page = max(1, page)
        limit = max(1, limit)
        offset = (page - 1) * limit

        total_users = await self.collection.count_documents() # theo id class
        total_pages = (total_users + limit - 1) // limit if total_users > 0 else 1

        if page > total_pages and total_pages > 0:
            page = total_pages
            offset = (page - 1) * limit

        users_cursor = await self.collection.find().skip(offset).limit(limit) # theo id class

        if users_cursor:
            list_users = []
            for user in users_cursor:
                user["id"] = str(user["_id"])
                list_users.append(UserResponse.model_validate(user))
    
            return list_users, total_pages, total_users
        
        return None, None, None
    

    async def update_user_infor(self, userID: str, user_info: UserUpdate) -> bool:
        query = {"_id": ObjectId(userID)}

        update_data = user_info.model_dump(exclude=True)

        if not update_data:
            return False
        
        result = await self.collection.update_one(
            query,
            {"$set": update_data}
        )

        return result.matched_count > 0
    

    async def delete_user(self, userID: str) -> bool:
        try:
            query = {"_id": ObjectId(userID)}
        except Exception:
            return False

        result = await self.collection.delete_one(query)
        
        return result.deleted_count > 0

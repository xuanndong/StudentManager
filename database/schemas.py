from pydantic import BaseModel

class UserRequest(BaseModel):
    username: str
    password: str
    role: str = "teacher" # student | admin

class UserResponse(BaseModel):
    id: str
    username: str
    role: str

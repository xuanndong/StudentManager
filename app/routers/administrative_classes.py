from fastapi import APIRouter, Depends, HTTPException, status, Request
from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv

from app.model.madministrative_class import AdministrativeClassCreate, AdministrativeClassResponse
from app.model.muser import UserResponse
from app.dependencies import get_current_cvht, get_current_user

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/administrative-classes", tags=['Administrative Classes (CVHT)'])


@router.post('/', response_model=AdministrativeClassResponse)
async def create_administrative_class(
    class_in: AdministrativeClassCreate,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    """CVHT tạo lớp chính quy"""
    db: AsyncDatabase = request.app.state.db

    class_dict = class_in.model_dump()
    class_dict.update({
        "advisor_id": str(current_user["_id"]),
        "student_ids": [],
        "created_at": datetime.now()
    })

    new_class = await db.administrative_classes.insert_one(class_dict)
    created_class = await db.administrative_classes.find_one({"_id": new_class.inserted_id})
    created_class["_id"] = str(created_class["_id"])

    return created_class


@router.get("/", response_model=list[AdministrativeClassResponse])
async def get_my_administrative_classes(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    - ADMIN: Xem tất cả các lớp
    - CVHT: Xem các lớp mình quản lý
    - STUDENT: Xem lớp chính quy của mình
    """
    db: AsyncDatabase = request.app.state.db

    if current_user.get('role') == "ADMIN":
        filter_query = {}  # Admin sees all classes
    elif current_user.get('role') == "CVHT":
        filter_query = {'advisor_id': str(current_user['_id'])}
    elif current_user.get('role') == "STUDENT":
        filter_query = {"student_ids": str(current_user["_id"])}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    classes = await db.administrative_classes.find(filter_query).to_list(length=None)

    for c in classes:
        c["_id"] = str(c["_id"])
    
    return classes


@router.get('/{class_id}/students', response_model=list[UserResponse])
async def get_class_students(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Xem danh sách sinh viên trong lớp chính quy"""
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")

    class_obj = await db.administrative_classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    if user_role != "ADMIN" and user_id != class_obj["advisor_id"] and user_id not in class_obj["student_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    student_ids = class_obj.get("student_ids", [])
    if not student_ids:
        return []
    
    student_obj_ids = [ObjectId(sid) for sid in student_ids if ObjectId.is_valid(sid)]
    students = await db.users.find({"_id": {"$in": student_obj_ids}}).to_list(length=None)

    for s in students:
        s["_id"] = str(s["_id"])
        if "password" in s:
            del s["password"]
    
    return students


@router.get('/{class_id}', response_model=AdministrativeClassResponse)
async def get_class_detail(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Xem chi tiết lớp chính quy"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    class_obj = await db.administrative_classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    class_obj["_id"] = str(class_obj["_id"])
    return class_obj


@router.delete("/{class_id}/students/{student_id}")
async def remove_student(
    class_id: str,
    student_id: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    """CVHT xóa sinh viên khỏi lớp chính quy"""
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")

    # Admin can access all classes, CVHT only their own
    if current_user.get('role') == "ADMIN":
        class_obj = await db.administrative_classes.find_one({"_id": ObjectId(class_id)})
    else:
        class_obj = await db.administrative_classes.find_one({
            "_id": ObjectId(class_id),
            "advisor_id": str(current_user["_id"])
        })

    if not class_obj:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    await db.administrative_classes.update_one(
        {"_id": ObjectId(class_id)},
        {"$pull": {"student_ids": student_id}}
    )
    
    # Xóa administrative_class_id của sinh viên
    if ObjectId.is_valid(student_id):
        await db.users.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {"administrative_class_id": None}}
        )

    return {"message": "Student removed from class"}

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime
from bson import ObjectId
import pandas as pd
import os
import io
from dotenv import load_dotenv

from app.model.mclass import ClassCreate, ClassResponse
from app.dependencies import get_current_cvht, get_current_user
from app.model.muser import UserResponse


# Load .env file
load_dotenv()


router = APIRouter(prefix=os.getenv("API_V1_STR","/api/v1") + "/classes", tags=['Classes'])


@router.post('/', response_model=ClassResponse)
async def create_class(class_in: ClassCreate, request: Request, current_user: dict = Depends(get_current_cvht)) -> ClassResponse:
    db: AsyncDatabase = request.app.state.db

    class_dict = class_in.model_dump()
    class_dict.update({
        "advisor_id": str(current_user["_id"]), # Liên kết với CVHT đang login
        "student_ids": [], # Ban đầu chưa có SV
        "created_at": datetime.now()
    })

    new_class = await db.classes.insert_one(class_dict)
    created_class = await db.classes.find_one({"_id": new_class.inserted_id})
    created_class["_id"] = str(created_class["_id"])

    return created_class


@router.get("/", response_model=list[ClassResponse])
async def get_my_classes(request: Request, semester: str | None = None, current_user: dict = Depends(get_current_user)) -> list:
    db: AsyncDatabase = request.app.state.db

    filter_query = {}
    if current_user.get('role') == "CVHT":
        filter_query = {'advisor_id': str(current_user['_id'])}
    else:
        filter_query = {"student_ids": str(current_user["_id"])}

    if semester and semester != "ALL":
        filter_query["semester"] = semester
        
    class_dict = await db.classes.find(filter_query).to_list(length=None)

    for c in class_dict:
        c["_id"] = str(c["_id"])
    
    return class_dict


@router.post("/{class_id}/import-students")
async def import_students(
    class_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_cvht)
):
    db: AsyncDatabase = request.app.state.db

    try:
        class_obj = await db.classes.find_one({"_id": ObjectId(class_id), "advisor_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class id format")
    
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found or you represent not the advisor")
    
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv or .xlsx files are supported")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse file: {str(e)}")
    

    imported_users = []
    errors = []

    # Chuẩn hóa tên cột về chữ thường để dễ xử lý 
    df.columns = [c.lower() for c in df.columns]

    target_column = None
    if 'email' in df.columns:
        target_column = 'email'
    elif 'mssv' in df.columns:
        target_column = 'mssv'
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must contain 'email' or 'mssv' column")
    
    # Lặp qua từng dòng
    for index, row in df.iterrows():
        val = str(row[target_column]).strip()

        # Find user in DB
        user = None
        if target_column == 'email':
            user = await db.users.find_one({'email': val})
        else:
            user = await db.users.find_one({'mssv': val})

        if user:
            imported_users.append(str(user['_id']))
        else:
            errors.append(f"Row {index+2}: User {val} not found in system")

    # Update in DB
    if imported_users:
        await db.classes.update_one(
            {"_id": ObjectId(class_id)},
            {"$addToSet": {"student_ids": {"$each": imported_users}}}
        )

    return {
        "message": "Import process completed",
        "added_count": len(imported_users),
        "errors": errors # Trả về danh sách lỗi để CVHT biết ai chưa được thêm
    }


@router.get('/{class_id}/students', response_model=list[UserResponse])
async def get_class_students(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user) # Cả SV và CVHT đều xem được
):
    db: AsyncDatabase = request.app.state.db

    try:
        class_obj = await db.classes.find_one({"_id": ObjectId(class_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")

    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    # Kiểm tra quyền: User phải là CVHT của lớp hoặc là thành viên của lớp
    user_id = str(current_user["_id"])

    if user_id != class_obj["advisor_id"] and user_id not in class_obj["student_ids"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a menber of this class")
    
    student_ids = class_obj.get("student_ids", [])
    if student_ids:
        student_obj_ids = [ObjectId(id_str) for id_str in student_ids]

    students = await db.users.find({"_id": {"$in": student_obj_ids}}).to_list(length=None)

    for s in students:
        s["_id"] = str(s["_id"])
    
    return students


@router.get('/{class_id}', response_model=ClassResponse)
async def get_class_detail(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    class_obj = await db.classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    class_obj["_id"] = str(class_obj["_id"])
    return class_obj


@router.delete("/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    db: AsyncDatabase = request.app.state.db

    # Kiểm tra quyền sở hữu
    class_chk = await db.classes.find_one({
        "_id": ObjectId(class_id),
        "advisor_id": str(current_user["_id"])
    })

    if not class_chk:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied or Class not found")
    
    # Dùng $pull xóa phần tử khỏi mảng
    result = await db.classes.update_one(
        {"_id": ObjectId(class_id)},
        {"$pull": {"student_ids": student_id}}
    )

    if result.modified_count == 0:
        return {"message": "Student not found in class or already removed"}
    
    return {"message": f"Student {student_id} removed from class"}

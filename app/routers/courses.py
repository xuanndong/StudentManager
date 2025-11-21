from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime
from bson import ObjectId
import pandas as pd
import io
import os
from dotenv import load_dotenv

from app.model.mcourse import CourseCreate, CourseUpdate, CourseResponse, CourseClassCreate, CourseClassResponse
from app.model.muser import UserResponse
from app.dependencies import get_current_admin, get_current_teacher, get_current_user

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1"), tags=['Courses & Course Classes'])


# ============ QUẢN LÝ MÔN HỌC (ADMIN) ============

@router.post('/courses', response_model=CourseResponse)
async def create_course(
    course_in: CourseCreate,
    request: Request,
    current_user: dict = Depends(get_current_admin)
):
    """Admin tạo môn học mới"""
    db: AsyncDatabase = request.app.state.db

    # Check duplicate course code
    existing = await db.courses.find_one({"code": course_in.code})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Course code already exists")

    course_dict = course_in.model_dump()
    course_dict["created_at"] = datetime.now()

    new_course = await db.courses.insert_one(course_dict)
    created_course = await db.courses.find_one({"_id": new_course.inserted_id})
    created_course["_id"] = str(created_course["_id"])

    return created_course


@router.get('/courses', response_model=list[CourseResponse])
async def get_all_courses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Lấy danh sách tất cả môn học"""
    db: AsyncDatabase = request.app.state.db

    courses = await db.courses.find().skip(skip).limit(limit).to_list(length=limit)

    for c in courses:
        c["_id"] = str(c["_id"])

    return courses


@router.get('/courses/{course_id}', response_model=CourseResponse)
async def get_course_detail(
    course_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Xem chi tiết môn học"""
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID")

    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    course["_id"] = str(course["_id"])
    return course


# ============ QUẢN LÝ LỚP HỌC PHẦN (TEACHER) ============

@router.post('/course-classes', response_model=CourseClassResponse)
async def create_course_class(
    course_class_in: CourseClassCreate,
    request: Request,
    current_user: dict = Depends(get_current_teacher)
):
    """Giáo viên tạo lớp học phần"""
    db: AsyncDatabase = request.app.state.db

    # Validate course exists
    if not ObjectId.is_valid(course_class_in.course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID")

    course = await db.courses.find_one({"_id": ObjectId(course_class_in.course_id)})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    class_dict = course_class_in.model_dump()
    class_dict.update({
        "teacher_id": str(current_user["_id"]),
        "student_ids": [],
        "created_at": datetime.now()
    })

    new_class = await db.course_classes.insert_one(class_dict)
    created_class = await db.course_classes.find_one({"_id": new_class.inserted_id})
    created_class["_id"] = str(created_class["_id"])

    return created_class


@router.get('/course-classes', response_model=list[CourseClassResponse])
async def get_my_course_classes(
    request: Request,
    semester: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    - TEACHER: Xem các lớp học phần mình dạy
    - STUDENT: Xem các lớp học phần mình đăng ký
    """
    db: AsyncDatabase = request.app.state.db

    filter_query = {}
    if current_user.get('role') == "TEACHER":
        filter_query = {'teacher_id': str(current_user['_id'])}
    elif current_user.get('role') == "STUDENT":
        filter_query = {"student_ids": str(current_user["_id"])}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if semester:
        filter_query["semester"] = semester
        
    classes = await db.course_classes.find(filter_query).to_list(length=None)

    # Populate course name
    for c in classes:
        c["_id"] = str(c["_id"])
        
        # Get course info
        course_id = c.get("course_id")
        if course_id and ObjectId.is_valid(course_id):
            course = await db.courses.find_one({"_id": ObjectId(course_id)})
            if course:
                c["course_name"] = course.get("name", "")
                c["course_code"] = course.get("code", "")
                c["credits"] = course.get("credits", 0)
    
    return classes


@router.post("/course-classes/{class_id}/import-students")
async def import_students_to_course_class(
    class_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_teacher)
):
    """Giáo viên import danh sách sinh viên vào lớp học phần"""
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    class_obj = await db.course_classes.find_one({
        "_id": ObjectId(class_id),
        "teacher_id": str(current_user["_id"])
    })
    
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found or access denied")
    
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv or .xlsx supported")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Parse error: {str(e)}")
    
    df.columns = [c.lower().strip() for c in df.columns]

    target_column = None
    if 'email' in df.columns:
        target_column = 'email'
    elif 'mssv' in df.columns:
        target_column = 'mssv'
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must contain 'email' or 'mssv' column")
    
    imported_users = []
    errors = []

    for index, row in df.iterrows():
        val = str(row[target_column]).strip()

        user = None
        if target_column == 'email':
            user = await db.users.find_one({'email': val, 'role': 'STUDENT'})
        else:
            user = await db.users.find_one({'mssv': val, 'role': 'STUDENT'})

        if user:
            user_id = str(user['_id'])
            if user_id not in imported_users:
                imported_users.append(user_id)
        else:
            errors.append(f"Row {index+2}: Student {val} not found")

    if imported_users:
        await db.course_classes.update_one(
            {"_id": ObjectId(class_id)},
            {"$addToSet": {"student_ids": {"$each": imported_users}}}
        )

    return {
        "message": "Import completed",
        "added_count": len(imported_users),
        "errors": errors
    }


@router.get('/course-classes/{class_id}/students', response_model=list[UserResponse])
async def get_course_class_students(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Xem danh sách sinh viên trong lớp học phần"""
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")

    class_obj = await db.course_classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    user_id = str(current_user["_id"])
    if user_id != class_obj["teacher_id"] and user_id not in class_obj["student_ids"]:
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


@router.get('/course-classes/{class_id}', response_model=CourseClassResponse)
async def get_course_class_detail(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Xem chi tiết lớp học phần"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    class_obj = await db.course_classes.find_one({"_id": ObjectId(class_id)})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    
    class_obj["_id"] = str(class_obj["_id"])
    return class_obj


@router.delete("/course-classes/{class_id}/students/{student_id}")
async def remove_student_from_course_class(
    class_id: str,
    student_id: str,
    request: Request,
    current_user: dict = Depends(get_current_teacher)
):
    """Giáo viên xóa sinh viên khỏi lớp học phần"""
    db: AsyncDatabase = request.app.state.db

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")

    class_obj = await db.course_classes.find_one({
        "_id": ObjectId(class_id),
        "teacher_id": str(current_user["_id"])
    })

    if not class_obj:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    await db.course_classes.update_one(
        {"_id": ObjectId(class_id)},
        {"$pull": {"student_ids": student_id}}
    )

    return {"message": "Student removed from course class"}


@router.put('/courses/{course_id}', response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_in: CourseUpdate,
    request: Request,
    current_user: dict = Depends(get_current_admin)
):
    """Admin cập nhật môn học"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID")
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    # Update course (code cannot be changed)
    update_data = {"name": course_in.name, "credits": course_in.credits}
    if course_in.grade_formula:
        update_data["grade_formula"] = course_in.grade_formula.model_dump()
    
    await db.courses.update_one({"_id": ObjectId(course_id)}, {"$set": update_data})
    
    updated_course = await db.courses.find_one({"_id": ObjectId(course_id)})
    updated_course["_id"] = str(updated_course["_id"])
    
    return updated_course


@router.delete('/courses/{course_id}')
async def delete_course(
    course_id: str,
    request: Request,
    current_user: dict = Depends(get_current_admin)
):
    """Admin xóa môn học"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(course_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid course ID")
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    # Delete course
    await db.courses.delete_one({"_id": ObjectId(course_id)})
    
    # Optionally: Delete related course_classes
    await db.course_classes.delete_many({"course_id": course_id})
    
    return {"message": "Course deleted successfully"}

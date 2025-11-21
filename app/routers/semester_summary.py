from fastapi import APIRouter, Depends, HTTPException, status, Request
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

from app.model.mgrade import SemesterSummaryResponse, SemesterSummaryUpdate
from app.dependencies import get_current_cvht, get_current_user

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/semester-summary", tags=['Semester Summary (CVHT)'])


from app.utils.grade_calculator import convert_to_gpa_4, is_passing_grade


async def calculate_semester_gpa(db: AsyncDatabase, student_id: str, semester: str) -> dict:
    """Tính GPA học kỳ từ điểm các môn"""
    
    # Get all course classes in this semester
    course_classes = await db.course_classes.find({
        "semester": semester,
        "student_ids": student_id
    }).to_list(length=None)
    
    if not course_classes:
        return {
            "gpa": 0.0,
            "credits_earned": 0,
            "credits_passed": 0
        }
    
    class_ids = [str(c["_id"]) for c in course_classes]
    
    # Get grades for these classes
    grades = await db.course_grades.find({
        "course_class_id": {"$in": class_ids},
        "student_id": student_id
    }).to_list(length=None)
    
    total_weighted_score = 0.0
    total_credits = 0
    credits_passed = 0
    
    for grade in grades:
        course_class_id = grade["course_class_id"]
        
        # Find course class to get course_id
        course_class = next((c for c in course_classes if str(c["_id"]) == course_class_id), None)
        if not course_class:
            continue
            
        # Get course info to get credits
        course = await db.courses.find_one({"_id": ObjectId(course_class["course_id"])})
        if not course:
            continue
            
        credits = course.get("credits", 0)
        total_score = grade.get("total_score")
        
        if total_score is not None:
            # Convert to 4.0 scale
            score_4 = convert_to_gpa_4(total_score)
            total_weighted_score += score_4 * credits
            total_credits += credits
            
            # Check if passed (>= 4.0 in 10 scale)
            if is_passing_grade(total_score):
                credits_passed += credits
    
    gpa = (total_weighted_score / total_credits) if total_credits > 0 else 0.0
    
    return {
        "gpa": round(gpa, 2),
        "credits_earned": total_credits,
        "credits_passed": credits_passed
    }


@router.post("/calculate/{student_id}")
async def calculate_and_save_semester_summary(
    student_id: str,
    semester: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    """CVHT tính toán và lưu tổng kết học kỳ cho sinh viên"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student ID")
    
    # Check if student belongs to CVHT's class
    student = await db.users.find_one({"_id": ObjectId(student_id), "role": "STUDENT"})
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    admin_class_id = student.get("administrative_class_id")
    if admin_class_id:
        admin_class = await db.administrative_classes.find_one({
            "_id": ObjectId(admin_class_id),
            "advisor_id": str(current_user["_id"])
        })
        if not admin_class:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student not in your class")
    
    # Calculate GPA
    result = await calculate_semester_gpa(db, student_id, semester)
    
    # Save to database
    await db.semester_summaries.update_one(
        {
            "student_id": student_id,
            "semester": semester
        },
        {
            "$set": {
                "gpa": result["gpa"],
                "credits_earned": result["credits_earned"],
                "credits_passed": result["credits_passed"],
                "updated_at": datetime.now()
            },
            "$setOnInsert": {
                "tuition_debt": False,
                "academic_warning": 0
            }
        },
        upsert=True
    )
    
    return {
        "message": "Semester summary calculated",
        "data": result
    }


@router.post("/calculate-class/{class_id}")
async def calculate_class_semester_summary(
    class_id: str,
    semester: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    """CVHT tính toán tổng kết học kỳ cho cả lớp"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    # Validate ownership
    admin_class = await db.administrative_classes.find_one({
        "_id": ObjectId(class_id),
        "advisor_id": str(current_user["_id"])
    })
    
    if not admin_class:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    student_ids = admin_class.get("student_ids", [])
    if not student_ids:
        return {"message": "No students in class", "processed": 0}
    
    processed = 0
    for student_id in student_ids:
        result = await calculate_semester_gpa(db, student_id, semester)
        
        await db.semester_summaries.update_one(
            {
                "student_id": student_id,
                "semester": semester
            },
            {
                "$set": {
                    "gpa": result["gpa"],
                    "credits_earned": result["credits_earned"],
                    "credits_passed": result["credits_passed"],
                    "updated_at": datetime.now()
                },
                "$setOnInsert": {
                    "tuition_debt": False,
                    "academic_warning": 0
                }
            },
            upsert=True
        )
        processed += 1
    
    return {
        "message": "Class semester summary calculated",
        "processed": processed
    }


@router.get("/my-summary", response_model=list[SemesterSummaryResponse])
async def get_my_semester_summary(
    request: Request,
    semester: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """Sinh viên xem tổng kết học kỳ của mình"""
    db: AsyncDatabase = request.app.state.db
    
    if current_user.get("role") != "STUDENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can view their summary")
    
    user_id = str(current_user["_id"])
    query = {"student_id": user_id}
    
    if semester:
        query["semester"] = semester
    
    summaries = await db.semester_summaries.find(query).sort("semester", -1).to_list(length=100)
    
    for s in summaries:
        s["_id"] = str(s["_id"])
    
    return summaries


@router.get("/class/{class_id}", response_model=list[SemesterSummaryResponse])
async def get_class_semester_summary(
    class_id: str,
    semester: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    """CVHT xem tổng kết học kỳ của lớp"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    # Validate ownership
    admin_class = await db.administrative_classes.find_one({
        "_id": ObjectId(class_id),
        "advisor_id": str(current_user["_id"])
    })
    
    if not admin_class:
        raise HTTPException(status_code=403, detail="Access denied")
    
    student_ids = admin_class.get("student_ids", [])
    if not student_ids:
        return []
    
    summaries = await db.semester_summaries.find({
        "student_id": {"$in": student_ids},
        "semester": semester
    }).to_list(length=1000)
    
    # Populate student names
    for s in summaries:
        s["_id"] = str(s["_id"])
        
        # Get student info
        student_id = s.get("student_id")
        if student_id and ObjectId.is_valid(student_id):
            student = await db.users.find_one({"_id": ObjectId(student_id)})
            if student:
                s["student_name"] = student.get("full_name", "Unknown")
                s["student_mssv"] = student.get("mssv", "")
    
    return summaries


@router.put("/{summary_id}", response_model=SemesterSummaryResponse)
async def update_semester_summary(
    summary_id: str,
    update_data: SemesterSummaryUpdate,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    """CVHT cập nhật thông tin nợ học phí, cảnh báo học vụ"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(summary_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid summary ID")
    
    summary = await db.semester_summaries.find_one({"_id": ObjectId(summary_id)})
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    
    # Check if student belongs to CVHT's class
    student_id = summary["student_id"]
    student = await db.users.find_one({"_id": ObjectId(student_id)})
    
    if student and student.get("administrative_class_id"):
        admin_class = await db.administrative_classes.find_one({
            "_id": ObjectId(student["administrative_class_id"]),
            "advisor_id": str(current_user["_id"])
        })
        if not admin_class:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now()
    
    await db.semester_summaries.update_one(
        {"_id": ObjectId(summary_id)},
        {"$set": update_dict}
    )
    
    updated_summary = await db.semester_summaries.find_one({"_id": ObjectId(summary_id)})
    updated_summary["_id"] = str(updated_summary["_id"])
    
    return updated_summary

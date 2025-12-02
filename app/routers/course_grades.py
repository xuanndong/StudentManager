from fastapi import APIRouter, Depends, HTTPException, status, Request
from pymongo.asynchronous.database import AsyncDatabase
from pymongo import UpdateOne
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.model.mgrade import CourseGradeResponse, CourseGradeImport
from app.dependencies import get_current_teacher, get_current_user

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/course-grades", tags=['Course Grades (Teacher)'])

# Pydantic models for save grades endpoint
class GradeData(BaseModel):
    student_id: str
    regular_score_1: Optional[float] = None
    regular_score_2: Optional[float] = None
    final_score: Optional[float] = None

class SaveGradesRequest(BaseModel):
    course_class_id: str
    grades: List[GradeData]


@router.post("/update")
async def update_student_grade(
    request: Request,
    grade_data: CourseGradeImport,
    current_user: dict = Depends(get_current_teacher)
):
    """Giáo viên cập nhật điểm cho một sinh viên"""
    db: AsyncDatabase = request.app.state.db
    
    # Validate class ownership
    if not ObjectId.is_valid(grade_data.course_class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    
    class_obj = await db.course_classes.find_one({
        "_id": ObjectId(grade_data.course_class_id),
        "teacher_id": str(current_user["_id"])
    })
    
    if not class_obj:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate student is in class
    if grade_data.student_id not in class_obj.get("student_ids", []):
        raise HTTPException(status_code=400, detail="Student not in this class")
    
    # Get course formula for auto-calculation
    course_id = class_obj.get("course_id")
    regular_w1 = 0.2
    regular_w2 = 0.3
    final_w = 0.5
    
    if course_id and ObjectId.is_valid(course_id):
        course = await db.courses.find_one({"_id": ObjectId(course_id)})
        if course:
            formula = course.get("grade_formula", {})
            regular_w1 = formula.get("regular_weight_1", 0.2)
            regular_w2 = formula.get("regular_weight_2", 0.3)
            final_w = formula.get("final_weight", 0.5)
    
    # Calculate total score
    from app.utils.grade_calculator import calculate_total_score
    total_score = calculate_total_score(
        grade_data.regular_score_1,
        grade_data.regular_score_2,
        grade_data.final_score,
        regular_w1, regular_w2, final_w
    )
    
    # Update or insert grade
    result = await db.course_grades.update_one(
        {
            "course_class_id": grade_data.course_class_id,
            "student_id": grade_data.student_id
        },
        {
            "$set": {
                "regular_score_1": grade_data.regular_score_1,
                "regular_score_2": grade_data.regular_score_2,
                "final_score": grade_data.final_score,
                "total_score": total_score,
                "updated_at": datetime.now()
            }
        },
        upsert=True
    )
    
    return {
        "message": "Grade updated successfully",
        "total_score": total_score
    }


@router.get("/my-grades", response_model=list[CourseGradeResponse])
async def get_my_course_grades(
    request: Request,
    semester: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """Sinh viên xem điểm các môn học của mình"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])

    if current_user.get("role") != "STUDENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can view their grades")

    query = {"student_id": user_id}
    
    if semester:
        course_classes = await db.course_classes.find({"semester": semester}).to_list(length=None)
        class_ids = [str(c["_id"]) for c in course_classes]
        query["course_class_id"] = {"$in": class_ids}

    records = await db.course_grades.find(query).to_list(length=100)
    
    # Populate course info
    for r in records:
        r["_id"] = str(r["_id"])
        
        # Get course class to get course_id and semester
        course_class_id = r.get("course_class_id")
        if course_class_id and ObjectId.is_valid(course_class_id):
            course_class = await db.course_classes.find_one({"_id": ObjectId(course_class_id)})
            if course_class:
                r["semester"] = course_class.get("semester", "N/A")
                r["class_code"] = course_class.get("class_code", "N/A")
                
                # Get course info
                course_id = course_class.get("course_id")
                if course_id and ObjectId.is_valid(course_id):
                    course = await db.courses.find_one({"_id": ObjectId(course_id)})
                    if course:
                        r["course_name"] = course.get("name", "")
                        r["course_code"] = course.get("code", "")
                        r["credits"] = course.get("credits", 0)
        
    return records


@router.get("/my-stats")
async def get_my_course_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Sinh viên xem thống kê học tập real-time
    """
    from app.utils.grade_calculator import convert_to_gpa_4, is_passing_grade
    
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    
    if current_user.get("role") != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can view stats")
    
    # Get all course classes student is enrolled in
    course_classes = await db.course_classes.find({
        "student_ids": user_id
    }).to_list(length=None)
    
    if not course_classes:
        return {
            "overall_gpa": 0.0,
            "total_credits": 0,
            "passed_credits": 0,
            "semester_gpas": []
        }
    
    class_ids = [str(c["_id"]) for c in course_classes]
    
    # Get all grades
    grades = await db.course_grades.find({
        "course_class_id": {"$in": class_ids},
        "student_id": user_id
    }).to_list(length=None)
    
    # Calculate overall stats
    total_weighted_score = 0.0
    total_credits = 0
    passed_credits = 0
    semester_data = {}  # {semester: {weighted_score, credits}}
    
    for grade in grades:
        course_class_id = grade["course_class_id"]
        total_score = grade.get("total_score")
        
        if total_score is None:
            continue
        
        # Find course class
        course_class = next((c for c in course_classes if str(c["_id"]) == course_class_id), None)
        if not course_class:
            continue
        
        semester = course_class.get("semester", "Unknown")
        
        # Get course info
        course_id = course_class.get("course_id")
        if not course_id or not ObjectId.is_valid(course_id):
            continue
            
        course = await db.courses.find_one({"_id": ObjectId(course_id)})
        if not course:
            continue
        
        credits = course.get("credits", 0)
        if credits == 0:
            continue
        
        # Convert to GPA 4.0
        gpa_4 = convert_to_gpa_4(total_score)
        
        # Overall stats
        total_weighted_score += gpa_4 * credits
        total_credits += credits
        
        if is_passing_grade(total_score):
            passed_credits += credits
        
        # Semester stats
        if semester not in semester_data:
            semester_data[semester] = {"weighted_score": 0.0, "credits": 0}
        semester_data[semester]["weighted_score"] += gpa_4 * credits
        semester_data[semester]["credits"] += credits
    
    # Calculate overall GPA
    overall_gpa = round(total_weighted_score / total_credits, 2) if total_credits > 0 else 0.0
    
    # Calculate semester GPAs
    semester_gpas = []
    for semester, data in sorted(semester_data.items()):
        sem_gpa = round(data["weighted_score"] / data["credits"], 2) if data["credits"] > 0 else 0.0
        semester_gpas.append({
            "semester": semester,
            "gpa": sem_gpa,
            "credits": data["credits"]
        })
    
    return {
        "overall_gpa": overall_gpa,
        "total_credits": total_credits,
        "passed_credits": passed_credits,
        "semester_gpas": semester_gpas
    }


@router.get("/course-class/{class_id}", response_model=list[CourseGradeResponse])
async def get_course_class_grades(
    class_id: str,
    request: Request,
    current_user: dict = Depends(get_current_teacher)
):
    """Giáo viên xem bảng điểm lớp học phần"""
    db: AsyncDatabase = request.app.state.db
    
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    # Validate ownership
    class_obj = await db.course_classes.find_one({
        "_id": ObjectId(class_id),
        "teacher_id": str(current_user["_id"])
    })
    
    if not class_obj:
        raise HTTPException(status_code=403, detail="Access denied")

    records = await db.course_grades.find({"course_class_id": class_id}).to_list(length=1000)

    # Populate student names
    for r in records:
        r["_id"] = str(r["_id"])
        
        # Get student info
        student_id = r.get('student_id')
        if student_id and ObjectId.is_valid(student_id):
            student = await db.users.find_one({"_id": ObjectId(student_id)})
            if student:
                r['student_name'] = student.get('full_name', 'Unknown')
                r['student_mssv'] = student.get('mssv', 'N/A')
    
    return records


@router.post("/save")
async def save_course_grades(
    request: Request,
    grades_request: SaveGradesRequest,
    current_user: dict = Depends(get_current_teacher)
):
    """Giáo viên lưu điểm cho lớp học phần"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])
    course_class_id = grades_request.course_class_id
    grades_data = grades_request.grades
    
    # Debug logging
    print(f"\n=== SAVE GRADES DEBUG ===")
    print(f"Class ID: {course_class_id}")
    print(f"Number of grades: {len(grades_data)}")
    for i, grade in enumerate(grades_data[:3]):  # Print first 3
        print(f"Grade {i}: student_id={grade.student_id}, TX1={grade.regular_score_1}, TX2={grade.regular_score_2}, CK={grade.final_score}")
    
    if not ObjectId.is_valid(course_class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    # Verify teacher owns this class
    class_obj = await db.course_classes.find_one({
        "_id": ObjectId(course_class_id),
        "teacher_id": user_id
    })
    
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found or access denied")
    
    # Verify all students belong to this class
    # Convert ObjectId to string for comparison
    student_ids_in_class = set(str(sid) if isinstance(sid, ObjectId) else sid for sid in class_obj.get("student_ids", []))
    
    # Debug: Check student_ids format
    print(f"\nStudent IDs in class (first 3): {list(student_ids_in_class)[:3]}")
    print(f"Type of first student_id in class: {type(list(student_ids_in_class)[0]) if student_ids_in_class else 'empty'}")
    
    bulk_operations = []
    success_count = 0
    errors = []
    
    # Get grade formula for calculating total score
    course_id = class_obj.get("course_id")
    w1 = 0.2
    w2 = 0.3
    w3 = 0.5
    
    if course_id and ObjectId.is_valid(course_id):
        course = await db.courses.find_one({"_id": ObjectId(course_id)})
        if course:
            formula = course.get("grade_formula", {})
            w1 = formula.get("regular_weight_1", 0.2)
            w2 = formula.get("regular_weight_2", 0.3)
            w3 = formula.get("final_weight", 0.5)
    
    for grade_data in grades_data:
        student_id = grade_data.student_id
        
        # Check if student is in this class
        if student_id not in student_ids_in_class:
            errors.append(f"Student {student_id} not enrolled in this class")
            continue
        
        # Validate scores
        def validate_score(score):
            return score if score is not None and 0 <= score <= 10 else None
        
        regular_score_1 = validate_score(grade_data.regular_score_1)
        regular_score_2 = validate_score(grade_data.regular_score_2)
        final_score = validate_score(grade_data.final_score)
        
        # Calculate total score with weight redistribution
        from app.utils.grade_calculator import calculate_total_score
        total_score = calculate_total_score(regular_score_1, regular_score_2, final_score, w1, w2, w3)
        
        # Create update operation
        update_data = {
            "course_class_id": course_class_id,
            "student_id": student_id,
            "regular_score_1": regular_score_1,
            "regular_score_2": regular_score_2,
            "final_score": final_score,
            "total_score": total_score,
            "updated_at": datetime.now()
        }
        
        # Debug: Print update data for first student
        if success_count == 0:
            print(f"\nFirst update_data: {update_data}")
        
        op = UpdateOne(
            filter={
                "course_class_id": course_class_id,
                "student_id": student_id
            },
            update={"$set": update_data},
            upsert=True
        )
        bulk_operations.append(op)
        success_count += 1
    
    # Execute bulk operations
    if bulk_operations:
        result = await db.course_grades.bulk_write(bulk_operations)
        print(f"\nBulk write result: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_count}")
    
    print(f"=== END SAVE GRADES ===\n")
    
    return {
        "message": "Grades saved successfully",
        "success_count": success_count,
        "errors": errors
    }

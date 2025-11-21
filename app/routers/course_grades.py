from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from pymongo.asynchronous.database import AsyncDatabase
from pymongo import UpdateOne
from bson import ObjectId
from datetime import datetime
import pandas as pd
import io
import os
from dotenv import load_dotenv

from app.model.mgrade import CourseGradeResponse, CourseGradeImport
from app.dependencies import get_current_teacher, get_current_user

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/course-grades", tags=['Course Grades (Teacher)'])


@router.post("/import")
async def import_course_grades(
    course_class_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_teacher)
):
    """Giáo viên import điểm cho lớp học phần"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])

    if not ObjectId.is_valid(course_class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")

    class_obj = await db.course_classes.find_one({
        "_id": ObjectId(course_class_id),
        "teacher_id": user_id
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
            raise HTTPException(status_code=400, detail="Only .csv or .xlsx supported")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")
    
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Mapping columns
    required_map = {
        "mssv": ["mssv", "ma sinh vien", "mã sinh viên"],
        "midterm": ["midterm", "giua ky", "giữa kỳ", "diem gk"],
        "final": ["final", "cuoi ky", "cuối kỳ", "diem ck"],
        "assignment": ["assignment", "bai tap", "bài tập", "bt"],
        "total": ["total", "tong ket", "tổng kết", "diem tk"]
    }

    def find_col(target_keys):
        for col in df.columns:
            if col in target_keys:
                return col
        return None
    
    col_mssv = find_col(required_map["mssv"])
    if not col_mssv:
        raise HTTPException(status_code=400, detail="File must contain 'MSSV' column")

    col_midterm = find_col(required_map["midterm"])
    col_final = find_col(required_map["final"])
    col_assignment = find_col(required_map["assignment"])
    col_total = find_col(required_map["total"])

    # Get all students in class
    student_ids_in_class = class_obj.get("student_ids", [])
    if not student_ids_in_class:
        raise HTTPException(status_code=400, detail="No students in this class")

    # Get MSSV list from Excel
    excel_mssvs = df[col_mssv].astype(str).str.strip().tolist()
    
    # Find users
    users_cursor = db.users.find({"mssv": {"$in": excel_mssvs}, "role": "STUDENT"})
    users_list = await users_cursor.to_list(length=None)
    
    mssv_to_userid = {u['mssv']: str(u['_id']) for u in users_list}

    bulk_operations = []
    errors = []
    success_count = 0

    for index, row in df.iterrows():
        mssv_val = str(row[col_mssv]).strip()
        
        student_db_id = mssv_to_userid.get(mssv_val)
        if not student_db_id:
            errors.append(f"Row {index+2}: MSSV '{mssv_val}' not found")
            continue

        # Check if student is in this class
        if student_db_id not in student_ids_in_class:
            errors.append(f"Row {index+2}: Student '{mssv_val}' not enrolled in this class")
            continue

        # Parse scores
        def parse_score(col_name):
            if col_name and pd.notna(row[col_name]):
                try:
                    score = float(row[col_name])
                    if 0 <= score <= 10:
                        return score
                except:
                    pass
            return None

        midterm_score = parse_score(col_midterm)
        final_score = parse_score(col_final)
        assignment_score = parse_score(col_assignment)
        total_score = parse_score(col_total)

        # Auto calculate total if not provided - use course's grade formula
        if total_score is None:
            # Get course's grade formula
            course_id = class_obj.get("course_id")
            if course_id and ObjectId.is_valid(course_id):
                course = await db.courses.find_one({"_id": ObjectId(course_id)})
                if course:
                    formula = course.get("grade_formula", {})
                    midterm_w = formula.get("midterm_weight", 0.3)
                    final_w = formula.get("final_weight", 0.5)
                    assignment_w = formula.get("assignment_weight", 0.2)
                    
                    # Calculate using formula
                    from app.utils.grade_calculator import calculate_total_score
                    total_score = calculate_total_score(
                        midterm_score, final_score, assignment_score,
                        midterm_w, final_w, assignment_w
                    )

        op = UpdateOne(
            filter={
                "course_class_id": course_class_id,
                "student_id": student_db_id
            },
            update={
                "$set": {
                    "midterm_score": midterm_score,
                    "final_score": final_score,
                    "assignment_score": assignment_score,
                    "total_score": total_score,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        bulk_operations.append(op)
        success_count += 1

    if bulk_operations:
        await db.course_grades.bulk_write(bulk_operations)

    return {
        "message": "Import grades completed",
        "success_count": success_count,
        "errors": errors
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
                        r["course_name"] = course.get("name", "Empty")
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
    Tính toán trực tiếp từ course_grades, không phụ thuộc semester_summaries
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

    for r in records:
        r["_id"] = str(r["_id"])
    
    return records

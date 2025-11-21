from fastapi import APIRouter, Depends, Request, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
import os
from dotenv import load_dotenv

from app.model.mstats import DashboardStats, GPADistribution
from app.dependencies import get_current_cvht

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/stats", tags=['Statistics (CVHT)'])

@router.get("/dashboard/{class_id}", response_model=DashboardStats)
async def get_dashboard_stats(
    class_id: str,
    semester: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
) -> DashboardStats:
    """CVHT xem thống kê dashboard cho lớp chính quy"""
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user['_id'])

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    # Validate ownership
    admin_class = await db.administrative_classes.find_one({
        "_id": ObjectId(class_id),
        "advisor_id": user_id
    })
    
    if not admin_class:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    student_ids = admin_class.get("student_ids", [])
    
    stats = DashboardStats(
        class_id=class_id,
        semester=semester,
        gpa_distribution=GPADistribution()
    )

    stats.total_students = len(student_ids)

    # Calculate average GPA for each student across all semesters
    for student_id in student_ids:
        # Get all semester summaries for this student
        summaries = await db.semester_summaries.find({
            'student_id': student_id
        }).to_list(length=None)
        
        if not summaries:
            # No data, count as weak
            stats.gpa_distribution.weak += 1
            continue
        
        # Calculate average GPA across all semesters
        total_gpa = sum(s.get('gpa', 0.0) for s in summaries)
        avg_gpa = total_gpa / len(summaries)
        
        # Check warnings and debt from latest semester
        latest_summary = summaries[-1] if summaries else None
        if latest_summary:
            if latest_summary.get('academic_warning', 0) > 0:
                stats.warning_count += 1
            if latest_summary.get('tuition_debt', False):
                stats.debt_count += 1
        
        # Classify by average GPA
        if avg_gpa >= 3.6:
            stats.gpa_distribution.excellent += 1
        elif avg_gpa >= 3.2:
            stats.gpa_distribution.good += 1
        elif avg_gpa >= 2.5:
            stats.gpa_distribution.fair += 1
        elif avg_gpa >= 2.0:
            stats.gpa_distribution.average += 1
        else:
            stats.gpa_distribution.weak += 1

    return stats

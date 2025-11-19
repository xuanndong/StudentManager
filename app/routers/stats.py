from fastapi import APIRouter, Depends, Request, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from bson import ObjectId
import os
from dotenv import load_dotenv

from app.model.mstats import DashboardStats, GPADistribution
from app.dependencies import get_current_cvht


# Load .env file
load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/stats", tags=['Statistics'])

@router.get("/dashboard/{class_id}", response_model=DashboardStats)
async def get_dashboard_stats(
    class_id: str,
    semester: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
) -> DashboardStats:
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user['_id'])

    try:
        class_obj = await db.classes.find_one({
            "_id": ObjectId(class_id),
            "advisor_id": user_id
        })
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class ID")
    
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied or class not found")
    
    records = await db.academic_records.find({
        'class_id': class_id,
        "semester": semester
    }).to_list(length=None)

    stats = DashboardStats(
        class_id=class_id,
        semester=semester,
        gpa_distribution=GPADistribution()
    )

    stats.total_students = len(records)

    for r in records:
        if r.get('academic_warning', 0) > 0:
            stats.warning_count += 1

        if r.get('tuition_debt', False):
            stats.debt_count += 1

        gpa = r.get('gpa', 0.0)
        if gpa >= 3.6:
            stats.gpa_distribution.excellent += 1
        elif gpa >= 3.2:
            stats.gpa_distribution.good += 1
        elif gpa >= 2.5:
            stats.gpa_distribution.fair += 1
        elif gpa >= 2.0:
            stats.gpa_distribution.average += 1
        else:
            stats.gpa_distribution.weak += 1

    return stats

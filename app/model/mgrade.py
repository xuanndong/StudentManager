from pydantic import BaseModel, Field
from datetime import datetime

class AcademicRecordBase(BaseModel):
    semester: str = Field(..., examples=['2025-1']) # Học kỳ
    gpa: float = Field(..., ge=0.0, le=4.0, examples=[3.2])
    credits_earned: int = Field(..., ge=0) # Số tín chỉ tích lũy kỳ này
    tuition_debt: bool = False # Có nợ học phí không
    academic_warning: int = 0 # Mức cảnh báo: 0, 1, 2, 3


class GradeImport(AcademicRecordBase):
    mssv: str # Dùng khi import từ Excel

class GradeResponse(AcademicRecordBase):
    id: str = Field(..., alias="_id")
    student_id: str # MSSV
    class_id: str | None = None # Có thể null nếu không gắn chặt với lớp
    updated_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "student_id": [],
                    "class_id": "",
                    "semester": "",
                    "gpa": 0,
                    "credits_earned": 0,
                    "tuition_debt": True,
                    "academic_warning": 0,
                    "updated_at": ""
                }
            ]
        }
    }

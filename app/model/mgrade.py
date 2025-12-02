from pydantic import BaseModel, Field
from datetime import datetime

# Điểm từng môn học
class CourseGradeBase(BaseModel):
    regular_score_1: float | None = Field(None, ge=0.0, le=10.0, description="Điểm thường xuyên 1")
    regular_score_2: float | None = Field(None, ge=0.0, le=10.0, description="Điểm thường xuyên 2")
    final_score: float | None = Field(None, ge=0.0, le=10.0, description="Điểm cuối kỳ")
    total_score: float | None = Field(None, ge=0.0, le=10.0, description="Điểm tổng kết")


class CourseGradeImport(CourseGradeBase):
    mssv: str  # Dùng khi import từ Excel


class CourseGradeResponse(CourseGradeBase):
    id: str = Field(..., alias="_id")
    course_class_id: str  # Lớp học phần
    student_id: str  # ID sinh viên
    updated_at: datetime
    
    course_name: str | None = None  # Tên môn học
    course_code: str | None = None  # Mã môn học
    class_code: str | None = None  # Mã lớp học phần
    semester: str | None = None  # Học kỳ
    credits: int | None = None  # Số tín chỉ

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


# Tổng kết học kỳ (tự động tính từ điểm các môn)
class SemesterSummaryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    student_id: str
    semester: str
    gpa: float = Field(..., ge=0.0, le=4.0)  # Điểm trung bình hệ 4
    credits_earned: int = Field(..., ge=0)  # Tín chỉ tích lũy trong kỳ
    credits_passed: int = Field(..., ge=0)  # Tín chỉ đạt (>= 4.0)
    tuition_debt: bool = False  # Nợ học phí
    academic_warning: int = 0  # Cảnh báo học vụ: 0, 1, 2, 3
    updated_at: datetime
    
    student_name: str | None = None  # Tên sinh viên
    student_mssv: str | None = None  # MSSV sinh viên

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class SemesterSummaryUpdate(BaseModel):
    tuition_debt: bool | None = None
    academic_warning: int | None = Field(None, ge=0, le=3)

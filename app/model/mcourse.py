from pydantic import BaseModel, Field
from datetime import datetime

class GradeFormula(BaseModel):
    """Công thức tính điểm môn học"""
    midterm_weight: float = 0.3  # Trọng số giữa kỳ (30%)
    final_weight: float = 0.5    # Trọng số cuối kỳ (50%)
    assignment_weight: float = 0.2  # Trọng số bài tập (20%)


class CourseBase(BaseModel):
    code: str = Field(..., examples=["IT3080"])  # Mã môn học
    name: str = Field(..., examples=["Lập trình Python"])
    credits: int = Field(..., ge=1, le=6, examples=[3])  # Số tín chỉ


class CourseCreate(CourseBase):
    grade_formula: GradeFormula | None = None  # Công thức tính điểm (mặc định 30-50-20)


class CourseResponse(CourseBase):
    id: str = Field(..., alias="_id")
    grade_formula: GradeFormula | None = None
    created_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


# Lớp học phần (Course Class)
class CourseClassCreate(BaseModel):
    course_id: str  # ID môn học
    semester: str = Field(..., examples=["2024-1"])  # Học kỳ
    class_code: str = Field(..., examples=["IT3080.01"])  # Mã lớp học phần


class CourseClassResponse(BaseModel):
    id: str = Field(..., alias="_id")
    course_id: str
    semester: str
    class_code: str | None = None  # Optional để tương thích với data cũ có "group"
    group: str | None = None  # Deprecated, giữ lại để tương thích
    teacher_id: str  # ID giáo viên
    student_ids: list[str] = []  # Danh sách sinh viên đăng ký
    created_at: datetime
    # Populated fields (optional)
    course_name: str | None = None  # Tên môn học (populated)
    course_code: str | None = None  # Mã môn học (populated)
    credits: int | None = None  # Số tín chỉ (populated)

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "course_id": "",
                    "semester": "2024-1",
                    "class_code": "IT3080.01",
                    "teacher_id": "",
                    "student_ids": [],
                    "created_at": "",
                    "course_name": "Lập trình Python",
                    "course_code": "IT3080"
                }
            ]
        }
    }

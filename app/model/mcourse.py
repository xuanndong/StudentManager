from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

class GradeFormula(BaseModel):
    """Công thức tính điểm môn học"""
    regular_weight_1: float = 0.2  # Trọng số thường xuyên 1 (20%)
    regular_weight_2: float = 0.3  # Trọng số thường xuyên 2 (30%)
    final_weight: float = 0.5      # Trọng số cuối kỳ (50%)
    
    @field_validator('regular_weight_1', 'regular_weight_2', 'final_weight')
    @classmethod
    def validate_weight(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Weight must be between 0 and 1')
        return v
    
    @model_validator(mode='after')
    def validate_total_weight(self):
        total = self.regular_weight_1 + self.regular_weight_2 + self.final_weight
        if not 0.99 <= total <= 1.01:  # Allow small floating point errors
            raise ValueError(f'Total weight must equal 1.0, got {total}')
        return self


class CourseBase(BaseModel):
    code: str = Field(..., examples=["IT3080"])  # Mã môn học
    name: str = Field(..., examples=["Lập trình Python"])
    credits: int = Field(..., ge=1, le=6, examples=[3])  # Số tín chỉ


class CourseCreate(CourseBase):
    grade_formula: GradeFormula | None = None  # Công thức tính điểm (mặc định 20-30-50)


class CourseUpdate(BaseModel):
    """Model for updating course"""
    name: str = Field(..., examples=["Lập trình Python"])
    credits: int = Field(..., ge=1, le=6, examples=[3])
    grade_formula: GradeFormula | None = None


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
    class_code: str | None = None
    teacher_id: str  # ID giáo viên
    student_ids: list[str] = []  # Danh sách sinh viên đăng ký
    created_at: datetime
    
    course_name: str | None = None  # Tên môn học 
    course_code: str | None = None  # Mã môn học
    credits: int | None = None  # Số tín chỉ 

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

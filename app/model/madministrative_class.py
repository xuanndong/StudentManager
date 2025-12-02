from pydantic import BaseModel, Field
from datetime import datetime

class AdministrativeClassCreate(BaseModel):
    name: str = Field(..., examples=["CNTT"])
    academic_year: str = Field(..., examples=["2020-2024"])  # Khóa học


class AdministrativeClassResponse(AdministrativeClassCreate):
    id: str = Field(..., alias="_id")
    advisor_id: str  # ID của CVHT
    student_ids: list[str] = []  # List user_id của sinh viên
    created_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "name": "CNTT",
                    "academic_year": "2020-2024",
                    "advisor_id": "",
                    "student_ids": [],
                    "created_at": ""
                }
            ]
        }
    }

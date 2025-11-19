from pydantic import BaseModel, Field
from datetime import datetime

class ClassCreate(BaseModel):
    name: str = Field(..., examples=["CNTT-K17"])
    semester: str = Field(..., examples=["2025-1"])


class ClassResponse(ClassCreate):
    id: str = Field(..., alias="_id")
    advisor_id: str # ID of CVHT
    student_ids: list[str] = [] # List mssv of student in class
    created_at: datetime

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "",
                    "advisor_id": "",
                    "student_ids": [],
                    "name": "",
                    "semester": "",
                    "created_at": ""
                }
            ]
        }
    }

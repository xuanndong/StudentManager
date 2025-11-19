from pydantic import BaseModel

class GPADistribution(BaseModel):
    excellent: int = 0 # Xuất sắc (3.6 - 4.0)
    good: int = 0 # Giỏi (3.2 - 3.59)
    fair: int = 0 # Khá (2.5 - 3.19)
    average: int = 0 # Trung bình (2.0 - 2.49)
    weak: int = 0 # Yếu (< 2,0)

class DashboardStats(BaseModel):
    class_id: str
    semester: str
    total_students: int = 0
    warning_count: int = 0
    debt_count: int = 0
    gpa_distribution: GPADistribution

"""
Utility functions for grade calculation
"""

def calculate_total_score(
    regular_1: float | None, 
    regular_2: float | None, 
    final: float | None,
    regular_weight_1: float = 0.2, 
    regular_weight_2: float = 0.3, 
    final_weight: float = 0.5
) -> float | None:
    """
    Tính điểm tổng kết theo công thức có trọng số
    
    Args:
        regular_1: Điểm thường xuyên 1
        regular_2: Điểm thường xuyên 2
        final: Điểm cuối kỳ
        regular_weight_1: Trọng số thường xuyên 1 (mặc định 20%)
        regular_weight_2: Trọng số thường xuyên 2 (mặc định 30%)
        final_weight: Trọng số cuối kỳ (mặc định 50%)
    
    Returns:
        Điểm tổng kết (0-10) hoặc None nếu thiếu điểm cuối kỳ
    """
    # Cần có ít nhất điểm cuối kỳ
    if final is None:
        return None
    
    # Nếu thiếu điểm thường xuyên, phân bổ lại trọng số
    if regular_1 is None and regular_2 is None:
        # Chỉ có điểm cuối kỳ
        return round(final, 2)
    elif regular_1 is None:
        # Có regular_2 và final
        total_weight = regular_weight_2 + final_weight
        return round((regular_2 * regular_weight_2 + final * final_weight) / total_weight, 2)
    elif regular_2 is None:
        # Có regular_1 và final
        total_weight = regular_weight_1 + final_weight
        return round((regular_1 * regular_weight_1 + final * final_weight) / total_weight, 2)
    
    # Tính điểm đầy đủ
    total = (regular_1 * regular_weight_1 + 
             regular_2 * regular_weight_2 + 
             final * final_weight)
    
    return round(total, 2)


def convert_to_gpa_4(score_10: float) -> float:
    """
    Chuyển đổi điểm hệ 10 sang hệ 4
    
    Thang điểm:
    8.5-10.0  -> 4.0 (A)
    8.0-8.4  -> 3.5 (B+)
    7.0-7.9  -> 3.0 (B)
    6.5-6.9  -> 2.5 (C+)
    5.5-6.4  -> 2.0 (C)
    5.0-5.4  -> 1.5 (D+)
    4.0-4.9  -> 1.0 (D)
    < 4.0    -> 0.0 (F)
    """
    if score_10 >= 8.5:
        return 4.0
    elif score_10 >= 8.0:
        return 3.5
    elif score_10 >= 7.0:
        return 3.0
    elif score_10 >= 6.5:
        return 2.5
    elif score_10 >= 5.5:
        return 2.0
    elif score_10 >= 5.0:
        return 1.5
    elif score_10 >= 4.0:
        return 1.0
    else:
        return 0.0


def is_passing_grade(score_10: float) -> bool:
    """Kiểm tra điểm có đạt không (>= 4.0)"""
    return score_10 >= 4.0


def calculate_semester_gpa(course_grades: list[dict], courses_info: dict) -> tuple[float, int, int]:
    """
    Tính GPA và tín chỉ cho học kỳ
    """
    total_grade_points = 0.0
    total_credits = 0
    passed_credits = 0
    
    for grade in course_grades:
        total_score = grade.get("total_score")
        if total_score is None:
            continue
        
        course_id = grade.get("course_id")
        course = courses_info.get(course_id, {})
        credits = course.get("credits", 0)
        
        if credits == 0:
            continue
        
        # Chuyển sang GPA 4.0
        gpa_4 = convert_to_gpa_4(total_score)
        
        # Tính điểm tích lũy
        total_grade_points += gpa_4 * credits
        total_credits += credits
        
        # Tín chỉ đạt
        if is_passing_grade(total_score):
            passed_credits += credits
    
    # Tính GPA trung bình
    gpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0
    
    return gpa, total_credits, passed_credits

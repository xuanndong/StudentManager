from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from pymongo.asynchronous.database import AsyncDatabase
from pymongo import UpdateOne
from bson import ObjectId
from datetime import datetime
import pandas as pd
import io
import os
from dotenv import load_dotenv


from app.model.mgrade import GradeResponse
from app.dependencies import get_current_cvht, get_current_user


# Load .env file
load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/grades", tags=['Academic Records'])

# API Import Bảng điểm (Chỉ CVHT)
@router.post("/import")
async def import_grades(
    class_id: str, # Import điểm cho lớp học
    semester: str, # Học kỳ nào
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])

    class_obj = await db.classes.find_one({"_id": ObjectId(class_id), "advisor_id": user_id})
    if not class_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found or permission denied")
    
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Only .csv or .xlsx files supported")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parse error: {str(e)}")
    
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Mapping cột (Header file Excel -> Database Field)
    # Cần quy định mẫu file Excel cho CVHT:
    # Cột bắt buộc: "mssv", "gpa" (hoặc "điểm"), "credits" (hoặc "tín chỉ")
    required_map = {
        "mssv": ["mssv", "ma sinh vien", "mã sinh viên"],
        "gpa": ["gpa", "diem", "điểm hệ 4", "tbchung"],
        "credits": ["credits", "tin chi", "tín chỉ", "số tc"],
        "warning": ["warning", "canh bao", "cảnh báo"],
        "debt": ["debt", "hoc phi", "nợ học phí"]
    }

    def find_col(target_keys):
        for col in df.columns:
            if col in target_keys:
                return col
        return None
    
    col_mssv = find_col(required_map["mssv"])
    col_gpa = find_col(required_map["gpa"])
    
    if not col_mssv or not col_gpa:
        raise HTTPException(status_code=400, detail="File must contain 'MSSV' and 'GPA' columns")

    col_credits = find_col(required_map["credits"])
    col_warning = find_col(required_map["warning"])
    col_debt = find_col(required_map["debt"])

    # Lấy tất cả MSSV trong file Excel ra 1 list
    excel_mssvs = df[col_mssv].astype(str).str.strip().tolist()
    
    # Tìm tất cả user có mssv nằm trong list đó
    users_cursor = db.users.find({"mssv": {"$in": excel_mssvs}})
    users_list = await users_cursor.to_list(length=None)
    
    # Tạo Map để tra cứu nhanh: {'20201234': 'object_id_cua_user'}
    mssv_to_userid = {u['mssv']: str(u['_id']) for u in users_list}

    bulk_operations = []
    errors = []
    success_count = 0

    for index, row in df.iterrows():
        mssv_val = str(row[col_mssv]).strip()
        
        # Check xem MSSV này có tồn tại trong DB không
        student_db_id = mssv_to_userid.get(mssv_val)
        if not student_db_id:
            errors.append(f"Row {index+2}: MSSV '{mssv_val}' not found in system")
            continue

        try:
            gpa_val = float(row[col_gpa])
            # Validate GPA logic (ví dụ 0 <= GPA <= 4.0)
            if not (0 <= gpa_val <= 4.0):
                 errors.append(f"Row {index+2}: GPA must be between 0 and 4.0")
                 continue
        except:
            errors.append(f"Row {index+2}: Invalid GPA format")
            continue

        # Lấy giá trị optional
        credits_val = int(row[col_credits]) if col_credits and pd.notna(row[col_credits]) else 0
        warning_val = int(row[col_warning]) if col_warning and pd.notna(row[col_warning]) else 0
        
        debt_val = False
        if col_debt and pd.notna(row[col_debt]):
            val_debt = str(row[col_debt]).lower()
            if val_debt in ['true', 'yes', 'co', 'có', 'x'] or (val_debt.isdigit() and int(val_debt) > 0):
                debt_val = True

        # Thay vì update ngay, tạo một operation và nhét vào danh sách chờ
        op = UpdateOne(
            filter={
                "student_id": student_db_id, 
                "semester": semester
            },
            update={
                "$set": {
                    "class_id": class_id,
                    "gpa": gpa_val,
                    "credits_earned": credits_val,
                    "tuition_debt": debt_val,
                    "academic_warning": warning_val,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        bulk_operations.append(op)
        success_count += 1

    # 4. Thực thi Bulk Write
    if bulk_operations:
        await db.academic_records.bulk_write(bulk_operations)

    return {
        "message": "Import grades completed",
        "success_count": success_count,
        "errors": errors
    }


# Xem điểm (Của chính mình - Dành cho SV)
@router.get("/my-grades", response_model=list[GradeResponse])
async def get_my_grades(
    request: Request,
    semester: str = None, # Optional filter
    current_user: dict = Depends(get_current_user)
):
    db: AsyncDatabase = request.app.state.db
    user_id = str(current_user["_id"])

    query = {"student_id": user_id}
    if semester:
        query["semester"] = semester

    records = await db.academic_records.find(query).sort("semester", -1).to_list(length=100)
    
    for r in records:
        r["_id"] = str(r["_id"])
        
    return records


# Xem bảng điểm của lớp (Dành cho CVHT)
@router.get("/class/{class_id}", response_model=list[GradeResponse])
async def get_class_grades(
    class_id: str,
    semester: str,
    request: Request,
    current_user: dict = Depends(get_current_cvht)
):
    db: AsyncDatabase = request.app.state.db
    
    # Validate Class Owner
    class_chk = await db.classes.find_one({"_id": ObjectId(class_id), "advisor_id": str(current_user["_id"])})
    if not class_chk:
        raise HTTPException(status_code=403, detail="Permission denied")

    query = {"class_id": class_id, "semester": semester}
    cursor = db.academic_records.find(query)
    records = await cursor.to_list(length=1000)

    for r in records:
        r["_id"] = str(r["_id"])
    
    return records
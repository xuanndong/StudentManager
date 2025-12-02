"""
Script để import sample data mới vào MongoDB
Dựa trên backend đã refactor với cấu trúc điểm mới
"""
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from datetime import datetime
from bson import ObjectId

load_dotenv()

async def import_sample_data():
    """Import sample data vào MongoDB"""
    
    # Kết nối database
    client = AsyncIOMotorClient(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", 27017))
    )
    db = client[os.getenv("DATABASE_NAME", "qlsv")]
    
    print("=" * 60)
    print("IMPORT SAMPLE DATA - BACKEND MỚI")
    print("=" * 60)
    print(f"Database: {os.getenv('DATABASE_NAME', 'qlsv')}")
    print("-" * 60)
    
    # Đọc file JSON
    with open('sample_data_new.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert ObjectId strings
    def convert_objectid(obj):
        if isinstance(obj, dict):
            if '$oid' in obj:
                return ObjectId(obj['$oid'])
            elif '$date' in obj:
                return datetime.fromisoformat(obj['$date'].replace('Z', '+00:00'))
            else:
                return {k: convert_objectid(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_objectid(item) for item in obj]
        else:
            return obj
    
    try:
        # Clear existing data
        print("\n🗑️  Xóa dữ liệu cũ...")
        await db.users.delete_many({})
        await db.courses.delete_many({})
        await db.administrative_classes.delete_many({})
        await db.course_classes.delete_many({})
        await db.course_grades.delete_many({})
        await db.semester_summaries.delete_many({})
        await db.posts.delete_many({})
        print("✓ Đã xóa dữ liệu cũ")
        
        # Import users
        print("\n👥 Import users...")
        users = convert_objectid(data['users'])
        result = await db.users.insert_many(users)
        print(f"✓ Đã import {len(result.inserted_ids)} users")
        
        # Import courses
        print("\n📚 Import courses...")
        courses = convert_objectid(data['courses'])
        result = await db.courses.insert_many(courses)
        print(f"✓ Đã import {len(result.inserted_ids)} courses")
        
        # Import administrative_classes
        print("\n🏫 Import administrative classes...")
        admin_classes = convert_objectid(data['administrative_classes'])
        result = await db.administrative_classes.insert_many(admin_classes)
        print(f"✓ Đã import {len(result.inserted_ids)} administrative classes")
        
        # Import course_classes
        print("\n📖 Import course classes...")
        course_classes = convert_objectid(data['course_classes'])
        result = await db.course_classes.insert_many(course_classes)
        print(f"✓ Đã import {len(result.inserted_ids)} course classes")
        
        # Import course_grades
        print("\n📊 Import course grades...")
        grades = convert_objectid(data['course_grades'])
        result = await db.course_grades.insert_many(grades)
        print(f"✓ Đã import {len(result.inserted_ids)} course grades")
        
        # Import semester_summaries
        print("\n📈 Import semester summaries...")
        summaries = convert_objectid(data['semester_summaries'])
        result = await db.semester_summaries.insert_many(summaries)
        print(f"✓ Đã import {len(result.inserted_ids)} semester summaries")
        
        # Import posts
        print("\n💬 Import posts...")
        posts = convert_objectid(data['posts'])
        result = await db.posts.insert_many(posts)
        print(f"✓ Đã import {len(result.inserted_ids)} posts")
        
        print("\n" + "=" * 60)
        print("✅ IMPORT HOÀN TẤT!")
        print("=" * 60)
        
        # Summary
        print("\n📋 TỔNG KẾT:")
        print(f"  - Users: {await db.users.count_documents({})}")
        print(f"  - Courses: {await db.courses.count_documents({})}")
        print(f"  - Administrative Classes: {await db.administrative_classes.count_documents({})}")
        print(f"  - Course Classes: {await db.course_classes.count_documents({})}")
        print(f"  - Course Grades: {await db.course_grades.count_documents({})}")
        print(f"  - Semester Summaries: {await db.semester_summaries.count_documents({})}")
        print(f"  - Posts: {await db.posts.count_documents({})}")
        
        print("\n👤 TÀI KHOẢN MẪU (Password: password123):")
        print("  - ADMIN: ADMIN001")
        print("  - CVHT: CVHT001")
        print("  - TEACHER: GV001")
        print("  - STUDENT: 20221234, 20221235, 20221236")
        
        print("\n📝 CẤU TRÚC ĐIỂM MỚI:")
        print("  - Thường xuyên 1: 20%")
        print("  - Thường xuyên 2: 30%")
        print("  - Cuối kỳ: 50%")
        
        print("\n🎯 CHẠY ỨNG DỤNG:")
        print("  Backend: python -m uvicorn app.main:app --reload --port 8080")
        print("  Frontend: python frontend/main.py")
        
    except Exception as e:
        print(f"\n❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(import_sample_data())

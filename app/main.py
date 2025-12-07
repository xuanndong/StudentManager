from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.db.connection import lifespan
from app.routers.auth import router as auth
from app.routers.users import router as user
from app.routers.administrative_classes import router as administrative_classes
from app.routers.courses import router as courses
from app.routers.course_grades import router as course_grades
from app.routers.semester_summary import router as semester_summary
from app.routers.posts import router as posts
from app.routers.chat import router as chat
from app.routers.stats import router as stats
from app.routers.ai_assistant import router as ai_assistant

load_dotenv()

app = FastAPI(
    lifespan=lifespan,
    title=os.getenv("PROJECT_NAME", "QLSV - Student Management System"),
    version="2.1.0",
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth)
app.include_router(user)
app.include_router(administrative_classes)
app.include_router(courses)
app.include_router(course_grades)
app.include_router(semester_summary)
app.include_router(posts)
app.include_router(chat)
app.include_router(stats)
app.include_router(ai_assistant)


@app.exception_handler(Exception)
async def generate_exception_handler(request: Request, exc: Exception):
    print(f"Error: {str(exc)}")

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error server"
    )


@app.get("/")
async def root():
    return {
        "message": "Student Management System API v2.1",
        "docs": "/docs",
    }


@app.get("/api/v1/classes")
async def deprecated_classes_endpoint():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={
            "error": "This endpoint has been removed",
            "message": "The /api/v1/classes endpoint is deprecated and no longer available.",
            "replacement": "Use /api/v1/administrative-classes for managing administrative classes (lớp chính quy)",
            "alternative": "Use /api/v1/course-classes for managing course classes (lớp học phần)"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)

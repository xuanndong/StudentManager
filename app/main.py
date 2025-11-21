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

# Deprecated routers (kept for backward compatibility)
from app.routers.classes import router as classes_deprecated
from app.routers.grades import router as grades_deprecated

load_dotenv()

app = FastAPI(
    lifespan=lifespan,
    title=os.getenv("PROJECT_NAME", "QLSV - Student Management System"),
    version="2.0.0",
    description="Refactored with proper separation: Administrative Classes (CVHT) and Course Classes (Teacher)",
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# New routers
app.include_router(auth)
app.include_router(user)
app.include_router(administrative_classes)
app.include_router(courses)
app.include_router(course_grades)
app.include_router(semester_summary)
app.include_router(posts)
app.include_router(chat)
app.include_router(stats)

# Deprecated routers (for backward compatibility)
app.include_router(classes_deprecated)
app.include_router(grades_deprecated)


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
        "message": "Student Management System API v2.0",
        "docs": "/docs",
        "note": "Refactored with proper business logic separation"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)

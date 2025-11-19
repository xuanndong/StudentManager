from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.db.connection import lifespan
from app.routers.auth import router as auth
from app.routers.users import router as user
from app.routers.classes import router as classes
from app.routers.posts import router as posts
from app.routers.grades import router as grades
from app.routers.chat import router as chat
from app.routers.stats import router as stats


# Load .env file
load_dotenv()

app = FastAPI(
    lifespan=lifespan,
    title=os.getenv("PROJECT_NAME", "QLSV"),
    version="1.0.0",
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
app.include_router(classes)
app.include_router(posts)
app.include_router(grades)
app.include_router(chat)
app.include_router(stats)


@app.exception_handler(Exception)
async def generate_exception_handler(request: Request, exc: Exception):
    print(f"Error: {str(exc)}")

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error server"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
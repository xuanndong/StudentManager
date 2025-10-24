# Standard Libraries
from contextlib import asynccontextmanager
import os

# Third-party Libraries
from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to DB")
    print("Creating AsyncEngine")
    # Tạo AsyncEngine (đối tượng quản lý kết nối)
    app.state.engine = create_async_engine(os.getenv("DATABASE_URL"), echo=True)

    # Khởi tạo CSDL
    
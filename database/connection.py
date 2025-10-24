# Standard Libraries
from contextlib import asynccontextmanager
import os

# Local Modules

# Third-party Liraries
from pymongo import AsyncMongoClient
from fastapi import FastAPI, Request
from dotenv import load_dotenv


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Connecting to DB')
    client = AsyncMongoClient(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", 27017))
    )

    app.state.db = client[os.getenv("DATABASE_NAME", "QLSV")]

    yield
    print("Closing connection")
    await client.close()


async def get_db(request: Request):
    return request.app.state.db


if __name__ == "__main__":
    import uvicorn

    app = FastAPI(lifespan=lifespan)

    uvicorn.run("connection:app", host="localhost", port=8000)
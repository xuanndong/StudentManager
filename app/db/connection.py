from pymongo import AsyncMongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import os
from contextlib import asynccontextmanager

# Load .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to MongoDB")
    app.state.client = AsyncMongoClient(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", 27017))
    )
    app.state.db = app.state.client[os.getenv("DATABASE_NAME", "data")]

    try:
        await app.state.db.users.create_index("mssv", unique=True)
    except Exception as e:
        print(f"Error when creating index: {str(e)}")

    yield
    print("Closing MongoDB connectiongs")
    await app.state.client.close()


async def get_db(request: Request):
    return request.app.state.db


app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.db.connection:app", host="0.0.0.0", port=8080, reload=True)
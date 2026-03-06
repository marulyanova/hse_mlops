import sys
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI

from routes import users, models, versions
from clients.postgres import get_pg_connection
from clients import s3


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with get_pg_connection() as conn:
            await conn.fetchval("SELECT 1")
    except Exception as e:
        raise

    s3.BASE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(users.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(versions.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": "Model Registry", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}

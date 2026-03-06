import sys
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
import logging

from routes import users, models, versions

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: проверка подключения к БД
    from clients.postgres import get_pg_connection

    try:
        async with get_pg_connection() as conn:
            await conn.fetchval("SELECT 1")
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # Инициализация хранилища
    from clients import s3

    s3.BASE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Storage initialized: {s3.BASE_STORAGE_PATH}")

    yield

    # Shutdown: очистка ресурсов (если нужно)
    logger.info("👋 Application shutting down")


app = FastAPI(
    title="Model Registry MVP",
    description="Simple model registry for MLOps",
    version="0.1.0",
    lifespan=lifespan,
)

# Подключаем маршруты
app.include_router(users.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(versions.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": "Model Registry MVP", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health_check():
    """Простая проверка здоровья сервиса."""
    return {"status": "ok"}

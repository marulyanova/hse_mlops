import asyncpg
from typing import AsyncGenerator
from contextlib import asynccontextmanager


@asynccontextmanager
async def get_pg_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    connection: asyncpg.Connection = await asyncpg.connect(
        user="postgres",
        password="postgres",
        database="model_registry",
        host="localhost",
        port=5432,
    )
    try:
        yield connection
    finally:
        await connection.close()

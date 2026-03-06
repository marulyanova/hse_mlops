from typing import Optional, List
from uuid import UUID

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from clients.postgres import get_pg_connection
from models.user import User, UserCreate


class UserRepository:

    # создать пользователя
    async def create(self, user: UserCreate) -> User:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (username, email, role)
                VALUES ($1, $2, $3)
                RETURNING id, username, email, role, created_at, updated_at
                """,
                user.username,
                user.email,
                user.role,
            )
            return User.model_validate(dict(row))

    # получить пользователя
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return User.model_validate(dict(row)) if row else None

    async def get_by_username(self, username: str) -> Optional[User]:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE username = $1", username
            )
            return User.model_validate(dict(row)) if row else None

    # список всех
    async def list_all(self) -> List[User]:
        async with get_pg_connection() as conn:
            rows = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
            return [User.model_validate(dict(row)) for row in rows]

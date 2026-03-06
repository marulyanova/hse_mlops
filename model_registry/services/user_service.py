from typing import Optional, List
from uuid import UUID

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from repositories.user_repo import UserRepository
from models.user import User, UserCreate


class UserService:

    def __init__(self):
        self.repo = UserRepository()

    async def create_user(self, user: UserCreate) -> User:
        # Проверка на дубликат
        existing = await self.repo.get_by_username(user.username)
        if existing:
            raise ValueError(f"User with username '{user.username}' already exists")
        return await self.repo.create(user)

    async def get_user(self, user_id: UUID) -> Optional[User]:
        return await self.repo.get_by_id(user_id)

    async def list_users(self) -> List[User]:
        return await self.repo.list_all()

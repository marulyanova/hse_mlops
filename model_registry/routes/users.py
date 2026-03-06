from fastapi import APIRouter, HTTPException, status
from uuid import UUID

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.user import User, UserCreate
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()


# Создание нового пользователя
@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    try:
        return await user_service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Получение информации о пользователе
@router.get("/{user_id}", response_model=User)
async def get_user(user_id: UUID):
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Список всех пользователей
@router.get("", response_model=list[User])
async def list_users():
    return await user_service.list_users()

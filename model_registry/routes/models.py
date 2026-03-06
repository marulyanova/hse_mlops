from fastapi import APIRouter, HTTPException, status, Query
from uuid import UUID
from typing import Optional

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.model import Model, ModelCreate, ModelUpdate
from services.model_service import ModelService
from services.user_service import UserService

router = APIRouter(prefix="/models", tags=["models"])
model_service = ModelService()


# Создание новой модели
@router.post("", response_model=Model, status_code=status.HTTP_201_CREATED)
async def create_model(
    model: ModelCreate,
    owner_id: UUID = Query(..., description="ID владельца (для демо)"),
):
    user_service = UserService()
    owner = await user_service.get_user(owner_id)
    if not owner:
        raise HTTPException(
            status_code=400, detail=f"Owner with id {owner_id} not found"
        )

    return await model_service.create_model(model, owner_id)


# Получение информации о модели
@router.get("/{model_id}", response_model=Model)
async def get_model(model_id: UUID):
    model = await model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


# Список моделей + фильтрация
@router.get("", response_model=list[Model])
async def list_models(
    owner_id: Optional[UUID] = Query(None, description="Фильтр по владельцу"),
    visibility: Optional[str] = Query(None, pattern="^(private|limited|public)$"),
):
    return await model_service.list_models(owner_id=owner_id, visibility=visibility)


# Обновление модели
@router.put("/{model_id}", response_model=Model)
async def update_model(
    model_id: UUID, update: ModelUpdate, requester_id: UUID = Query(...)
):
    updated = await model_service.update_model(model_id, update, requester_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")
    return updated


# Удаление модели
@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: UUID, requester_id: UUID = Query(...), requester_role: str = Query("user")
):
    success = await model_service.delete_model(model_id, requester_id, requester_role)
    if not success:
        raise HTTPException(
            status_code=404, detail="Model not found or permission denied"
        )
    return None


# Модель с полным списком версий
@router.get("/{model_id}/details")
async def get_model_with_versions(model_id: UUID):
    result = await model_service.get_model_with_versions(model_id)
    if not result:
        raise HTTPException(status_code=404, detail="Model not found")
    return result

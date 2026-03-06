from typing import Optional, List
from uuid import UUID

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from repositories.model_repo import ModelRepository
from models.model import Model, ModelCreate, ModelUpdate
from services.version_service import VersionService


class ModelService:

    def __init__(self):
        self.repo = ModelRepository()
        self.version_service = VersionService()

    async def create_model(self, model: ModelCreate, owner_id: UUID) -> Model:
        return await self.repo.create(model, owner_id)

    async def get_model(self, model_id: UUID) -> Optional[Model]:
        return await self.repo.get_by_id(model_id)

    async def list_models(
        self, owner_id: Optional[UUID] = None, visibility: Optional[str] = None
    ) -> List[Model]:
        if owner_id:
            return await self.repo.list_by_owner(owner_id)
        return await self.repo.list_all(visibility)

    async def update_model(
        self, model_id: UUID, update: ModelUpdate, requester_id: UUID
    ) -> Optional[Model]:
        model = await self.repo.get_by_id(model_id)
        if not model:
            return None

        # Предупреждение вместо реальной проверки прав для MVP уровня
        if model.owner_id != requester_id:
            print(
                f"Warning: User {requester_id} updated model {model_id} owned by {model.owner_id}"
            )

        return await self.repo.update(model_id, update)

    async def delete_model(
        self, model_id: UUID, requester_id: UUID, requester_role: str = "user"
    ) -> bool:
        model = await self.repo.get_by_id(model_id)
        if not model:
            return False

        # Только владелец или админ может удалять
        if requester_role != "admin" and model.owner_id != requester_id:
            print(
                f"Warning: User {requester_id} (role: {requester_role}) tried to delete model {model_id} owned by {model.owner_id}"
            )
            return False

        # Удаляем все версии модели
        versions = await self.version_service.list_versions(model_id)
        for v in versions:
            await self.version_service.delete_version(v.id, force=True)

        return await self.repo.delete(model_id)

    async def get_model_with_versions(self, model_id: UUID) -> Optional[dict]:
        model = await self.repo.get_by_id(model_id)
        if not model:
            return None

        versions = await self.version_service.list_versions(model_id)
        return {
            "model": model,
            "versions": versions,
            "production_version": next(
                (v for v in versions if v.status == "production"), None
            ),
        }

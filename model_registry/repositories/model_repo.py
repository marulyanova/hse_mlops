from typing import Optional, List
from uuid import UUID

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.postgres import get_pg_connection
from models.model import Model, ModelCreate, ModelUpdate


class ModelRepository:

    # создание модели
    async def create(self, model: ModelCreate, owner_id: UUID) -> Model:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO models (name, description, owner_id, visibility)
                VALUES ($1, $2, $3, $4)
                RETURNING id, name, description, owner_id, visibility, created_at, updated_at
                """,
                model.name,
                model.description,
                owner_id,
                model.visibility,
            )
            return Model.model_validate(dict(row))

    # получение модели по id
    async def get_by_id(self, model_id: UUID) -> Optional[Model]:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM models WHERE id = $1", model_id)
            return Model.model_validate(dict(row)) if row else None

    # получение всех моделей пользователя
    async def list_by_owner(self, owner_id: UUID) -> List[Model]:
        async with get_pg_connection() as conn:
            rows = await conn.fetch(
                "SELECT * FROM models WHERE owner_id = $1 ORDER BY created_at DESC",
                owner_id,
            )
            return [Model.model_validate(dict(row)) for row in rows]

    # получение всех моделей доступных
    async def list_all(self, visibility: Optional[str] = None) -> List[Model]:
        async with get_pg_connection() as conn:
            if visibility:
                rows = await conn.fetch(
                    "SELECT * FROM models WHERE visibility = $1 ORDER BY created_at DESC",
                    visibility,
                )
            else:
                rows = await conn.fetch("SELECT * FROM models ORDER BY created_at DESC")
            return [Model.model_validate(dict(row)) for row in rows]

    # обновление параметров модели
    async def update(self, model_id: UUID, update: ModelUpdate) -> Optional[Model]:
        async with get_pg_connection() as conn:
            updates = []
            values = []
            idx = 1

            if update.name is not None:
                updates.append(f"name = ${idx}")
                values.append(update.name)
                idx += 1
            if update.description is not None:
                updates.append(f"description = ${idx}")
                values.append(update.description)
                idx += 1
            if update.visibility is not None:
                updates.append(f"visibility = ${idx}")
                values.append(update.visibility)
                idx += 1

            if not updates:
                return await self.get_by_id(model_id)

            values.append(model_id)
            query = f"""
                UPDATE models 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${idx}
                RETURNING id, name, description, owner_id, visibility, created_at, updated_at
            """
            row = await conn.fetchrow(query, *values)
            return Model.model_validate(dict(row)) if row else None

    # удалить модель
    async def delete(self, model_id: UUID) -> bool:
        async with get_pg_connection() as conn:
            result = await conn.execute("DELETE FROM models WHERE id = $1", model_id)
            return result == "DELETE 1"

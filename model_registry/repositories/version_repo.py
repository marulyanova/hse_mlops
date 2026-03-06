from typing import Optional, List
from uuid import UUID
import json

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from clients.postgres import get_pg_connection
from models.version import Version, VersionCreate, VersionUpdate


class VersionRepository:
    """
    Создание, получение, обновление, удаление версий модели.
    Получение актуальной продакшн версии
    """

    async def create(
        self,
        version: VersionCreate,
        model_id: UUID,
        file_path: str,
        file_hash: str,
        file_size: int,
    ) -> Version:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO model_versions (
                    model_id, version, description, status,
                    file_path, file_hash, file_size,
                    data_info, code_info, environment, 
                    hyperparameters, metrics
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
                """,
                model_id,
                version.version,
                version.description,
                "staging",
                file_path,
                file_hash,
                file_size,
                json.dumps(version.data_info or {}),
                json.dumps(version.code_info or {}),
                json.dumps(version.environment or {}),
                json.dumps(version.hyperparameters or {}),
                json.dumps(version.metrics or {}),
            )
            return Version.model_validate(dict(row))

    async def get_by_id(self, version_id: UUID) -> Optional[Version]:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM model_versions WHERE id = $1", version_id
            )
            return Version.model_validate(dict(row)) if row else None

    async def get_by_model(self, model_id: UUID) -> List[Version]:
        async with get_pg_connection() as conn:
            rows = await conn.fetch(
                "SELECT * FROM model_versions WHERE model_id = $1 ORDER BY created_at DESC",
                model_id,
            )
            return [Version.model_validate(dict(row)) for row in rows]

    async def update(
        self, version_id: UUID, update: VersionUpdate
    ) -> Optional[Version]:
        async with get_pg_connection() as conn:
            updates = []
            values = []
            idx = 1

            if update.description is not None:
                updates.append(f"description = ${idx}")
                values.append(update.description)
                idx += 1
            if update.status is not None:
                updates.append(f"status = ${idx}")
                values.append(update.status)
                idx += 1
            if update.metrics is not None:
                updates.append(f"metrics = ${idx}")
                values.append(update.metrics)
                idx += 1

            if not updates:
                return await self.get_by_id(version_id)

            values.append(version_id)
            query = f"""
                UPDATE model_versions 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${idx}
                RETURNING *
            """
            row = await conn.fetchrow(query, *values)
            return Version.model_validate(dict(row)) if row else None

    async def delete(self, version_id: UUID) -> bool:
        async with get_pg_connection() as conn:
            result = await conn.execute(
                "DELETE FROM model_versions WHERE id = $1", version_id
            )
            return result == "DELETE 1"

    async def get_production_version(self, model_id: UUID) -> Optional[Version]:
        async with get_pg_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM model_versions WHERE model_id = $1 AND status = 'production' LIMIT 1",
                model_id,
            )
            return Version.model_validate(dict(row)) if row else None

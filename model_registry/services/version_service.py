import hashlib
from pathlib import Path
from typing import Optional, List
from uuid import UUID

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from repositories.version_repo import VersionRepository
from models.version import Version, VersionCreate, VersionUpdate
from clients import s3


class VersionService:

    def __init__(self):
        self.repo = VersionRepository()

    def _calculate_file_hash(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def create_version(
        self, model_id: UUID, version: VersionCreate, file_path: str
    ) -> Version:
        # хеш и размер файла
        file_hash = self._calculate_file_hash(file_path)
        file_size = Path(file_path).stat().st_size

        # ключ для хранилища: model_id/version/filename
        file_name = Path(file_path).name
        object_key = f"{model_id}/{version.version}/{file_name}"

        stored_path = await s3.upload_model_file(file_path, object_key)

        return await self.repo.create(
            version=version,
            model_id=model_id,
            file_path=stored_path,
            file_hash=file_hash,
            file_size=file_size,
        )

    async def get_version(self, version_id: UUID) -> Optional[Version]:
        return await self.repo.get_by_id(version_id)

    async def list_versions(self, model_id: UUID) -> List[Version]:
        return await self.repo.get_by_model(model_id)

    async def update_version(
        self, version_id: UUID, update: VersionUpdate
    ) -> Optional[Version]:
        return await self.repo.update(version_id, update)

    async def delete_version(self, version_id: UUID, force: bool = False) -> bool:
        version = await self.repo.get_by_id(version_id)
        if not version:
            return False

        # удаление из хранилища
        if force or version.status != "production":
            await s3.delete_model_file(version.file_path)

        return await self.repo.delete(version_id)

    async def set_status(self, version_id: UUID, status: str) -> Optional[Version]:
        if status not in ("staging", "production", "archived"):
            raise ValueError(f"Invalid status: {status}")

        # production должен быть один, поэтому убираем с других версий
        if status == "production":
            version = await self.repo.get_by_id(version_id)
            if version:
                all_versions = await self.repo.get_by_model(version.model_id)
                for v in all_versions:
                    if v.id != version_id and v.status == "production":
                        await self.repo.update(v.id, VersionUpdate(status="staging"))

        return await self.repo.update(version_id, VersionUpdate(status=status))

    async def download_version(self, version_id: UUID, dest_path: str) -> str:
        version = await self.repo.get_by_id(version_id)
        if not version:
            raise FileNotFoundError(f"Version {version_id} not found")

        return await s3.download_model_file(version.file_path, dest_path)

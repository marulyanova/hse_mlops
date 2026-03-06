from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from uuid import UUID
from typing import Optional
import tempfile
import shutil
import json

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.version import Version, VersionCreate, VersionUpdate
from services.version_service import VersionService

router = APIRouter(prefix="/models/{model_id}/versions", tags=["versions"])
version_service = VersionService()


# Создание новой версии модели с загрузкой файла
@router.post("", response_model=Version, status_code=status.HTTP_201_CREATED)
async def create_version(
    model_id: UUID,
    version: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    data_info: Optional[str] = Form(None),
    code_info: Optional[str] = Form(None),
    environment: Optional[str] = Form(None),
    hyperparameters: Optional[str] = Form(None),
    metrics: Optional[str] = Form(None),
):
    # Временное сохранение файла
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(file.filename).suffix
    ) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        version_data = VersionCreate(
            version=version,
            description=description,
            data_info=json.loads(data_info) if data_info else None,
            code_info=json.loads(code_info) if code_info else None,
            environment=json.loads(environment) if environment else None,
            hyperparameters=json.loads(hyperparameters) if hyperparameters else None,
            metrics=json.loads(metrics) if metrics else None,
        )

        return await version_service.create_version(model_id, version_data, tmp_path)

    finally:
        # Удаление временного файла
        Path(tmp_path).unlink(missing_ok=True)


# Список версий модели
@router.get("", response_model=list[Version])
async def list_versions(model_id: UUID):
    return await version_service.list_versions(model_id)


# Информация о конкретной версии
@router.get("/{version_id}", response_model=Version)
async def get_version(model_id: UUID, version_id: UUID):
    version = await version_service.get_version(version_id)
    if not version or version.model_id != model_id:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


# Обновление версии
@router.put("/{version_id}", response_model=Version)
async def update_version(model_id: UUID, version_id: UUID, update: VersionUpdate):
    version = await version_service.get_version(version_id)
    if not version or version.model_id != model_id:
        raise HTTPException(status_code=404, detail="Version not found")

    updated = await version_service.update_version(version_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Version not found")
    return updated


# Удаление версии
@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(model_id: UUID, version_id: UUID):
    version = await version_service.get_version(version_id)
    if not version or version.model_id != model_id:
        raise HTTPException(status_code=404, detail="Version not found")

    success = await version_service.delete_version(version_id)
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    return None


# Скачивание файла модели
@router.get("/{version_id}/download")
async def download_version(model_id: UUID, version_id: UUID):
    version = await version_service.get_version(version_id)
    if not version or version.model_id != model_id:
        raise HTTPException(status_code=404, detail="Version not found")

    # временный файл для отдачи
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await version_service.download_version(version_id, tmp_path)
        file_name = Path(version.file_path).name
        return FileResponse(
            tmp_path, filename=file_name, media_type="application/octet-stream"
        )
    finally:
        # файл будет удален после отдачи
        pass


# Изменение статуса версии
@router.put("/{version_id}/status", response_model=Version)
async def update_version_status(
    model_id: UUID,
    version_id: UUID,
    status: str = Query(..., pattern="^(staging|production|archived)$"),
):
    version = await version_service.get_version(version_id)
    if not version or version.model_id != model_id:
        raise HTTPException(status_code=404, detail="Version not found")

    updated = await version_service.set_status(version_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Version not found")
    return updated

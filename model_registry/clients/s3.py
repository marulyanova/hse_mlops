import os
import shutil
from pathlib import Path

# Для MVP: храним файлы локально, далее переход на S3
BASE_STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./storage/models"))
BASE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


async def upload_model_file(file_path: str, object_key: str) -> str:
    # Загрузка файла модели в хранилище, возвращает путь/ключ для последующего скачивания

    dest_path = BASE_STORAGE_PATH / object_key
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(file_path, dest_path)
    return object_key


async def download_model_file(object_key: str, dest_path: str) -> str:
    # Скачивание файла модели из хранилища, возвращает путь к скачанному файлу

    source_path = BASE_STORAGE_PATH / object_key
    if not source_path.exists():
        raise FileNotFoundError(f"Model file not found: {object_key}")

    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, dest_path)
    return dest_path


async def delete_model_file(object_key: str) -> bool:
    # Удаление файла модели из хранилища

    file_path = BASE_STORAGE_PATH / object_key
    if file_path.exists():
        file_path.unlink()
        return True
    return False

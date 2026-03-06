### Отчет

В файле hw2_model_registry.pdf

### Реализовано в рамках первичной версии

- Регистрация пользователя
- Создание/чтение/обновление/удаление модели
- Загрузка версии модели с файлом
- Хранение метаданных
- Управление статусами версий (staging/production/archived)
- Скачивание файлов моделей
- Базовая проверка прав (владелец/админ)
- Предупреждения в логах
- Хранение файлов (локально)

### Не реализовано, но указано в отчете

- Аутентификация
- Поиск и фильтрация по метрикам, тегам, автору
- Сравнение версий, diff метрик
- Квоты и лимиты, ограничение на размер/количество загрузок

### Подготовка к запуску сервиса

```sh
Создание БД
sudo -i -u postgres
psql
CREATE DATABASE model_registry

Создание папки для локального хранения моделей
mkdir -p ./storage/models

Запуск миграции для создания таблиц в БД
cd db
bash start_migration.sh

Запуск сервиса
uvicorn main:app --reload --port 8000
```

### Тестирование

1) Пользователи

```sh
- Пользователь создание
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user_1", "email": "test_user_1@example.com", "role": "user"}'

Должно вернуться:
{
    "id": "e86e71dd-8582-4c8a-af87-2fc8dbb4882f",
    "username": "test_user_1",
    "email": "test_user_1@example.com",
    "role": "user",
    "created_at": "2026-03-06T15:48:03.995184",
    "updated_at": "2026-03-06T15:48:03.995184"
}

- Админ создание
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username": "test_admin_1", "email": "test_admin_1@example.com", "role": "admin"}'

Должно вернуться:
{
    "id": "19d9414e-00dd-46c2-8437-3c6a9f29f066",
    "username": "test_admin_1",
    "email": "test_admin_1@example.com",
    "role": "admin",
    "created_at": "2026-03-06T15:48:45.402412",
    "updated_at": "2026-03-06T15:48:45.402412"
}

- Список всех пользователей
curl http://localhost:8000/api/v1/users

Должно вернуться:
[
    {
        "id": "19d9414e-00dd-46c2-8437-3c6a9f29f066",
        "username": "test_admin_1",
        "email": "test_admin_1@example.com",
        "role": "admin",
        "created_at": "2026-03-06T15:48:45.402412",
        "updated_at": "2026-03-06T15:48:45.402412"
    },
    {
        "id": "e86e71dd-8582-4c8a-af87-2fc8dbb4882f",
        "username": "test_user_1",
        "email": "test_user_1@example.com",
        "role": "user",
        "created_at": "2026-03-06T15:48:03.995184",
        "updated_at": "2026-03-06T15:48:03.995184"
    }
]

- Получение инфо по пользователю
curl http://localhost:8000/api/v1/users/e86e71dd-8582-4c8a-af87-2fc8dbb4882f

Должно вернуться:
{
    "id": "e86e71dd-8582-4c8a-af87-2fc8dbb4882f",
    "username": "test_user_1",
    "email": "test_user_1@example.com",
    "role": "user",
    "created_at": "2026-03-06T15:48:03.995184",
    "updated_at": "2026-03-06T15:48:03.995184"
}
```

2) Модели

```sh

- Создание модели от e86e71dd-8582-4c8a-af87-2fc8dbb4882f (test_user_1)
curl -X POST "http://localhost:8000/api/v1/models?owner_id=e86e71dd-8582-4c8a-af87-2fc8dbb4882f" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-classifier", "description": "Test model", "visibility": "private"}'

Должно вернуться:
{
    "id": "c26be8b2-7051-45c2-8bcf-0df956a0ac59",
    "name": "my-classifier",
    "description": "Test model",
    "owner_id": "e86e71dd-8582-4c8a-af87-2fc8dbb4882f",
    "visibility": "private",
    "created_at": "2026-03-06T17:03:20.188487",
    "updated_at": "2026-03-06T17:03:20.188487"
}

- Добавление 1 версии модели c26be8b2-7051-45c2-8bcf-0df956a0ac59
curl -X POST "http://localhost:8000/api/v1/models/c26be8b2-7051-45c2-8bcf-0df956a0ac59/versions" \
  -F "version=v1.0" \
  -F "description=First version" \
  -F "file=@mock/model_1.pkl" \
  -F 'metrics={"accuracy": 0.95, "f1": 0.93}'

Должно вернуться:
{
    "id": "a3985b7b-7eb0-4efc-a6fd-27109f8ed717",
    "model_id": "c26be8b2-7051-45c2-8bcf-0df956a0ac59",
    "version": "v1.0",
    "status": "staging",
    "description": "First version",
    "file_path": "c26be8b2-7051-45c2-8bcf-0df956a0ac59/v1.0/tmpgttib76s.pkl",
    "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "file_size": 0,
    "data_info": {},
    "code_info": {},
    "environment": {},
    "hyperparameters": {},
    "metrics": {
        "f1": 0.93,
        "accuracy": 0.95
    },
    "created_at": "2026-03-06T17:04:51.396443",
    "updated_at": "2026-03-06T17:04:51.396443"
}

- Добавление 2 версии модели c26be8b2-7051-45c2-8bcf-0df956a0ac59
curl -X POST "http://localhost:8000/api/v1/models/c26be8b2-7051-45c2-8bcf-0df956a0ac59/versions" \
  -F "version=v2.0" \
  -F "description=Second version" \
  -F "file=@mock/model_2.pkl" \
  -F 'metrics={"accuracy": 0.98, "f1": 0.95}'

Должно вернуться:
{
    "id": "d326f71d-8f43-4138-8264-2697d06d5223",
    "model_id": "c26be8b2-7051-45c2-8bcf-0df956a0ac59",
    "version": "v2.0",
    "status": "staging",
    "description": "Second version",
    "file_path": "c26be8b2-7051-45c2-8bcf-0df956a0ac59/v2.0/tmp47qm86x_.pkl",
    "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "file_size": 0,
    "data_info": {},
    "code_info": {},
    "environment": {},
    "hyperparameters": {},
    "metrics": {
        "f1": 0.95,
        "accuracy": 0.98
    },
    "created_at": "2026-03-06T17:06:01.769538",
    "updated_at": "2026-03-06T17:06:01.769538"
}

INFO:     127.0.0.1:51509 - "POST /api/v1/models/c26be8b2-7051-45c2-8bcf-0df956a0ac59/versions HTTP/1.1" 201 Created
INFO:     127.0.0.1:51528 - "POST /api/v1/models/c26be8b2-7051-45c2-8bcf-0df956a0ac59/versions HTTP/1.1" 201 Created

- Получение списка версий модели c26be8b2-7051-45c2-8bcf-0df956a0ac59
curl http://localhost:8000/api/v1/models/c26be8b2-7051-45c2-8bcf-0df956a0ac59/versions

Должно вернуться:
[
    {
        "id": "d326f71d-8f43-4138-8264-2697d06d5223",
        "model_id": "c26be8b2-7051-45c2-8bcf-0df956a0ac59",
        "version": "v2.0",
        "status": "staging",
        "description": "Second version",
        "file_path": "c26be8b2-7051-45c2-8bcf-0df956a0ac59/v2.0/tmp47qm86x_.pkl",
        "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "file_size": 0,
        "data_info": {},
        "code_info": {},
        "environment": {},
        "hyperparameters": {},
        "metrics": {
            "f1": 0.95,
            "accuracy": 0.98
        },
        "created_at": "2026-03-06T17:06:01.769538",
        "updated_at": "2026-03-06T17:06:01.769538"
    },
    {
        "id": "a3985b7b-7eb0-4efc-a6fd-27109f8ed717",
        "model_id": "c26be8b2-7051-45c2-8bcf-0df956a0ac59",
        "version": "v1.0",
        "status": "staging",
        "description": "First version",
        "file_path": "c26be8b2-7051-45c2-8bcf-0df956a0ac59/v1.0/tmpgttib76s.pkl",
        "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "file_size": 0,
        "data_info": {},
        "code_info": {},
        "environment": {},
        "hyperparameters": {},
        "metrics": {
            "f1": 0.93,
            "accuracy": 0.95
        },
        "created_at": "2026-03-06T17:04:51.396443",
        "updated_at": "2026-03-06T17:04:51.396443"
    }
]

- Скачать модель c26be8b2-7051-45c2-8bcf-0df956a0ac59 с версией d326f71d-8f43-4138-8264-2697d06d5223 (вторая версия)
curl -O http://localhost:8000/api/v1/models/c26be8b2-7051-45c2-8bcf-0df956a0ac59/versions/d326f71d-8f43-4138-8264-2697d06d5223/download

Было загружено

- Обновление модели, поменяем visibility
curl -X PUT "http://localhost:8000/api/v1/models/c26be8b2-7051-45c2-8bcf-0df956a0ac59?requester_id=e86e71dd-8582-4c8a-af87-2fc8dbb4882f" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated: model v2", "visibility": "public"}'

Должно вернуться:
{
    "id": "c26be8b2-7051-45c2-8bcf-0df956a0ac59",
    "name": "my-classifier",
    "description": "Updated: model v2",
    "owner_id": "e86e71dd-8582-4c8a-af87-2fc8dbb4882f",
    "visibility": "public",
    "created_at": "2026-03-06T17:03:20.188487",
    "updated_at": "2026-03-06T17:11:27.349776"
}

- Список моделей с фильтром по владельцу
curl "http://localhost:8000/api/v1/models?owner_id=e86e71dd-8582-4c8a-af87-2fc8dbb4882f"

- Список моделей с фильтром по видимости
curl "http://localhost:8000/api/v1/models?visibility=private"
```
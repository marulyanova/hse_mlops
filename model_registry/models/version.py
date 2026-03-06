from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
)
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import json


class VersionCreate(BaseModel):
    version: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    data_info: Optional[Dict[str, Any]] = None
    code_info: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None


class VersionUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(staging|production|archived)$")
    metrics: Optional[Dict[str, float]] = None


class Version(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    model_id: UUID
    version: str
    status: str
    description: Optional[str] = None
    file_path: str
    file_hash: str
    file_size: int
    data_info: Dict[str, Any] = Field(default_factory=dict)
    code_info: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, Any] = Field(default_factory=dict)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator(
        "data_info",
        "code_info",
        "environment",
        "hyperparameters",
        "metrics",
        mode="before",
    )
    @classmethod
    def parse_jsonb(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        return value if isinstance(value, dict) else {}

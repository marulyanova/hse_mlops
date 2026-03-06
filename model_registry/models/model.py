from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    visibility: str = Field(default="private", pattern="^(private|limited|public)$")


class ModelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(private|limited|public)$")


class Model(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    owner_id: UUID
    visibility: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

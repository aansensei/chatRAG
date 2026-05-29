from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import DocumentStatus, SensitivityLevel


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    original_filename: str
    file_path: str
    file_type: str
    file_size: int
    owner_id: UUID
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL
    status: DocumentStatus = DocumentStatus.PROCESSING
    page_count: int | None = None
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}

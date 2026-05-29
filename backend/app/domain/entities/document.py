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
    # relative path within storage, not an absolute path on disk
    file_path: str
    file_type: str
    file_size: int
    owner_id: UUID
    # default INTERNAL rather than PUBLIC — safer before classification completes
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL
    status: DocumentStatus = DocumentStatus.PROCESSING
    page_count: int | None = None
    language: str | None = None
    # store extra info without adding new DB columns
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # frozen=True means updated_at won't auto-update — create a new instance at the repo layer
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # frozen: never mutate in place, create a new instance to update a field
    model_config = {"frozen": True}

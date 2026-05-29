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
    # relative path trong storage, không phải absolute path trên disk
    file_path: str
    file_type: str
    file_size: int
    owner_id: UUID
    # default INTERNAL thay vì PUBLIC để an toàn hơn khi chưa classify xong
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL
    status: DocumentStatus = DocumentStatus.PROCESSING
    page_count: int | None = None
    language: str | None = None
    # dùng để lưu extra info mà không cần thêm column DB
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # frozen=True nên updated_at không tự update - phải tạo instance mới ở repo layer
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # frozen: không mutate trực tiếp, tạo instance mới để update field
    model_config = {"frozen": True}

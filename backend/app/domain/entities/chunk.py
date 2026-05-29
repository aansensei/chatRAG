from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str
    chunk_index: int
    # token_count cần estimate trước khi gọi embedding model để tránh exceed context limit
    token_count: int
    char_count: int
    page_number: int | None = None
    section_title: str | None = None
    # None cho đến khi vector_worker upsert vào Qdrant và nhận point ID về
    embedding_id: str | None = None
    # giữ heading hierarchy, slide number, ... để retrieval có thêm context
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}

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
    # estimate token_count before calling the embedding model to avoid exceeding context limits
    token_count: int
    char_count: int
    page_number: int | None = None
    section_title: str | None = None
    # None until vector_worker upserts into Qdrant and gets a point ID back
    embedding_id: str | None = None
    # stores heading hierarchy, slide number, etc. to give retrieval extra context
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import IngestJobStatus


class IngestJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    status: IngestJobStatus = IngestJobStatus.PENDING
    # human-readable string, not an enum — step labels may change between pipeline versions
    current_step: str | None = None
    error_message: str | None = None
    # None until chunking completes — use (embedded_chunks / total_chunks) * 100 for progress %
    total_chunks: int | None = None
    embedded_chunks: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}

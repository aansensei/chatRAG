from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import ReviewStatus


class Review(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    # None when no reviewer has been assigned — reviewer self-claims or admin assigns
    reviewer_id: UUID | None = None
    status: ReviewStatus = ReviewStatus.PENDING
    notes: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # only create a Review for documents with SensitivityLevel >= CONFIDENTIAL
    model_config = {"frozen": True}

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Permission(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    document_id: UUID
    can_read: bool = True
    can_edit: bool = False
    can_delete: bool = False
    granted_by: UUID
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    model_config = {"frozen": True}

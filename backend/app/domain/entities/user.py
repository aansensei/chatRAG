from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import UserRole


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    # EmailStr requires pydantic[email] installed (email-validator package)
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # password hash does not belong here — that's the auth service's concern
    model_config = {"frozen": True}

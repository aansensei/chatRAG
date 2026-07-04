import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.presentation.api.auth import get_current_user

router = APIRouter(prefix="/memory", tags=["memory"], dependencies=[Depends(get_current_user)])

_STORAGE = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
_MEMORY_FILE = _STORAGE / "memory.json"


def _load() -> list[dict[str, Any]]:
    if not _MEMORY_FILE.exists():
        return []
    try:
        return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items: list[dict[str, Any]]) -> None:
    _STORAGE.mkdir(parents=True, exist_ok=True)
    _MEMORY_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def migrate_legacy_memories() -> None:
    """One-time backfill: memories created before per-user scoping existed have no
    user_id and would otherwise become permanently invisible. Assign them to the
    first admin account (this system only had one user before this change)."""
    items = _load()
    if not any("user_id" not in m for m in items):
        return
    from app.infrastructure.storage.local.auth_store import list_users
    admin = next((u for u in list_users() if u["role"] == "admin"), None)
    if not admin:
        return
    for m in items:
        if "user_id" not in m:
            m["user_id"] = admin["id"]
    _save(items)


def get_memories(user_id: str | None = None) -> list[dict[str, Any]]:
    items = _load()
    if user_id is None:
        return items
    return [m for m in items if m.get("user_id") == user_id]


def add_memory_internal(content: str, user_id: str | None = None) -> dict[str, Any] | None:
    """Add a memory directly (called from auto-extract in retrieval). Skips duplicates
    within the same user's memories."""
    content = (content or "").strip()
    if not content or len(content.split()) > 3000:
        return None
    items = _load()
    norm = content.lower()
    for m in items:
        if m.get("user_id") == user_id and (m.get("content") or "").strip().lower() == norm:
            return None
    item = {"id": uuid.uuid4().hex[:12], "content": content, "created_at": int(time.time()), "auto": True, "user_id": user_id}
    items.append(item)
    _save(items)
    return item


class AddMemoryBody(BaseModel):
    content: str


@router.get("")
def list_memories(user: dict = Depends(get_current_user)):
    return get_memories(user["id"])


@router.post("")
def add_memory(body: AddMemoryBody, user: dict = Depends(get_current_user)):
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content cannot be empty")
    if len(content.split()) > 3000:
        raise HTTPException(status_code=400, detail="content too long (max 3000 words)")
    items = _load()
    item = {"id": uuid.uuid4().hex[:12], "content": content, "created_at": int(time.time()), "user_id": user["id"]}
    items.append(item)
    _save(items)
    return item


@router.delete("/{memory_id}")
def delete_memory(memory_id: str, user: dict = Depends(get_current_user)):
    items = _load()
    new_items = [m for m in items if not (m.get("id") == memory_id and m.get("user_id") == user["id"])]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Not found")
    _save(new_items)
    return {"ok": True}

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/memory", tags=["memory"])

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


def get_memories() -> list[dict[str, Any]]:
    return _load()


def add_memory_internal(content: str) -> dict[str, Any] | None:
    """Add a memory directly (called from auto-extract in retrieval). Skips duplicates."""
    content = (content or "").strip()
    if not content or len(content.split()) > 3000:
        return None
    items = _load()
    norm = content.lower()
    for m in items:
        if (m.get("content") or "").strip().lower() == norm:
            return None
    item = {"id": uuid.uuid4().hex[:12], "content": content, "created_at": int(time.time()), "auto": True}
    items.append(item)
    _save(items)
    return item


class AddMemoryBody(BaseModel):
    content: str


@router.get("")
def list_memories():
    return _load()


@router.post("")
def add_memory(body: AddMemoryBody):
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content cannot be empty")
    if len(content.split()) > 3000:
        raise HTTPException(status_code=400, detail="content too long (max 3000 words)")
    items = _load()
    item = {"id": uuid.uuid4().hex[:12], "content": content, "created_at": int(time.time())}
    items.append(item)
    _save(items)
    return item


@router.delete("/{memory_id}")
def delete_memory(memory_id: str):
    items = _load()
    new_items = [m for m in items if m.get("id") != memory_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Not found")
    _save(new_items)
    return {"ok": True}

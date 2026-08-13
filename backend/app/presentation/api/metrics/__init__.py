import json
import os
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Depends

from app.infrastructure.storage.local.admin_audit_store import list_admin_actions
from app.infrastructure.storage.local.auth_store import get_user_by_id
from app.presentation.api.auth import require_admin

_METRICS_FILE = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage")) / "metrics.jsonl"

router = APIRouter(prefix="/metrics", tags=["metrics"], dependencies=[Depends(require_admin)])


def _read_entries() -> list[dict]:
    if not _METRICS_FILE.exists():
        return []
    entries = []
    with open(_METRICS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


@router.get("/summary")
def get_metrics_summary():
    entries = _read_entries()
    total = len(entries)
    if not total:
        return {"total_queries": 0, "avg_latency_ms": 0, "error_count": 0, "by_model": {}}

    errors = sum(1 for e in entries if not e.get("success", True))
    avg_latency = round(sum(e.get("latency_ms", 0) for e in entries) / total)

    by_model: dict[str, dict] = defaultdict(lambda: {"count": 0, "avg_latency_ms": 0, "errors": 0})
    for e in entries:
        m = e.get("model") or "unknown"
        stats = by_model[m]
        stats["count"] += 1
        stats["avg_latency_ms"] += e.get("latency_ms", 0)
        if not e.get("success", True):
            stats["errors"] += 1
    for stats in by_model.values():
        stats["avg_latency_ms"] = round(stats["avg_latency_ms"] / stats["count"])

    by_user: dict[str, int] = defaultdict(int)
    for e in entries:
        uid = e.get("user_id")
        if uid:
            by_user[uid] += 1
    by_user_named = {}
    for uid, count in by_user.items():
        u = get_user_by_id(uid)
        by_user_named[u["email"] if u else uid] = count

    return {
        "total_queries": total,
        "avg_latency_ms": avg_latency,
        "error_count": errors,
        "by_model": dict(by_model),
        "by_user": by_user_named,
    }


@router.get("/audit")
def get_audit_log(user_email: str | None = None, limit: int = 100, offset: int = 0):
    """Raw query-level audit trail — who asked what, when, and which documents
    were surfaced. Newest first."""
    entries = _read_entries()
    entries.sort(key=lambda e: e.get("ts", 0), reverse=True)

    # Resolve user_id -> email once per unique id instead of per entry.
    email_cache: dict[str, str] = {}

    def _email_for(uid: str | None) -> str | None:
        if not uid:
            return None
        if uid not in email_cache:
            u = get_user_by_id(uid)
            email_cache[uid] = u["email"] if u else uid
        return email_cache[uid]

    rows = []
    for e in entries:
        email = _email_for(e.get("user_id"))
        if user_email and email != user_email:
            continue
        rows.append({
            "ts": e.get("ts"),
            "user_email": email,
            "question": e.get("question"),
            "model": e.get("model"),
            "collections": e.get("collections", []),
            "document_ids": e.get("document_ids", []),
            "latency_ms": e.get("latency_ms"),
            "success": e.get("success", True),
        })

    total = len(rows)
    return {"total": total, "rows": rows[offset:offset + limit]}


@router.get("/admin-audit")
def get_admin_audit_log(limit: int = 100, offset: int = 0):
    """Who did what to which user account, and when — create/delete/edit
    actions taken by admins on other users' accounts."""
    return list_admin_actions(limit, offset)

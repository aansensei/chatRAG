import json
import os
import time
from pathlib import Path

_AUDIT_FILE = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage")) / "admin_audit.jsonl"


def log_admin_action(actor: dict, action: str, target_user_id: str | None = None, target_email: str | None = None, details: dict | None = None) -> None:
    _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": int(time.time()),
        "actor_id": actor["id"],
        "actor_email": actor["email"],
        "action": action,
        "target_user_id": target_user_id,
        "target_email": target_email,
        "details": details or {},
    }
    with open(_AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def list_admin_actions(limit: int = 100, offset: int = 0) -> dict:
    if not _AUDIT_FILE.exists():
        return {"total": 0, "rows": []}
    rows = []
    with open(_AUDIT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return {"total": len(rows), "rows": rows[offset:offset + limit]}

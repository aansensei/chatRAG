import os
import sqlite3
import time
import uuid
from pathlib import Path

_STORAGE_DIR = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
_DB_PATH = _STORAGE_DIR / "rename_requests.db"


def _connect() -> sqlite3.Connection:
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS rename_requests ("
        "id TEXT PRIMARY KEY, requester_id TEXT NOT NULL, requester_email TEXT NOT NULL, "
        "collection TEXT NOT NULL, new_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', "
        "reason TEXT, created_at INTEGER NOT NULL, resolved_at INTEGER, resolved_by TEXT"
        ")"
    )
    return conn


def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "requester_id": row[1],
        "requester_email": row[2],
        "collection": row[3],
        "new_name": row[4],
        "status": row[5],
        "reason": row[6],
        "created_at": row[7],
        "resolved_at": row[8],
        "resolved_by": row[9],
    }


_COLUMNS = "id, requester_id, requester_email, collection, new_name, status, reason, created_at, resolved_at, resolved_by"


def create_request(requester_id: str, requester_email: str, collection: str, new_name: str) -> dict:
    conn = _connect()
    try:
        req_id = str(uuid.uuid4())
        created_at = int(time.time())
        conn.execute(
            "INSERT INTO rename_requests (id, requester_id, requester_email, collection, new_name, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
            (req_id, requester_id, requester_email, collection, new_name, created_at),
        )
        conn.commit()
        row = conn.execute(f"SELECT {_COLUMNS} FROM rename_requests WHERE id = ?", (req_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def list_requests(requester_id: str | None = None) -> list[dict]:
    """If requester_id is given, only that user's own requests are returned — used
    for non-admin callers who should not see other people's requests."""
    conn = _connect()
    try:
        if requester_id:
            rows = conn.execute(
                f"SELECT {_COLUMNS} FROM rename_requests WHERE requester_id = ? ORDER BY created_at DESC", (requester_id,)
            ).fetchall()
        else:
            rows = conn.execute(f"SELECT {_COLUMNS} FROM rename_requests ORDER BY created_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_request(request_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(f"SELECT {_COLUMNS} FROM rename_requests WHERE id = ?", (request_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def resolve_request(request_id: str, status: str, admin_id: str, reason: str | None = None) -> dict | None:
    conn = _connect()
    try:
        conn.execute(
            "UPDATE rename_requests SET status = ?, reason = ?, resolved_at = ?, resolved_by = ? WHERE id = ?",
            (status, reason, int(time.time()), admin_id, request_id),
        )
        conn.commit()
        row = conn.execute(f"SELECT {_COLUMNS} FROM rename_requests WHERE id = ?", (request_id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()

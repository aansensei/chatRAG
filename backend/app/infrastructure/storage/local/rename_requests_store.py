import os
import sqlite3
import time
import uuid
from pathlib import Path

# Despite the module/file name (kept for historical reasons — this used to only
# handle folder renames), this store now covers all KB approval requests:
# rename, delete, and add (a post-hoc confirmation for uploads that went live
# immediately but still need sign-off from someone with authority).
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
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(rename_requests)").fetchall()}
    if "request_type" not in existing_cols:
        conn.execute("ALTER TABLE rename_requests ADD COLUMN request_type TEXT NOT NULL DEFAULT 'rename'")
    if "document_id" not in existing_cols:
        conn.execute("ALTER TABLE rename_requests ADD COLUMN document_id TEXT")
    if "filename" not in existing_cols:
        conn.execute("ALTER TABLE rename_requests ADD COLUMN filename TEXT")
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
        "request_type": row[10],
        "document_id": row[11],
        "filename": row[12],
    }


_COLUMNS = (
    "id, requester_id, requester_email, collection, new_name, status, reason, created_at, "
    "resolved_at, resolved_by, request_type, document_id, filename"
)


def create_request(
    requester_id: str,
    requester_email: str,
    request_type: str,
    collection: str,
    new_name: str = "",
    document_id: str | None = None,
    filename: str | None = None,
) -> dict:
    conn = _connect()
    try:
        req_id = str(uuid.uuid4())
        created_at = int(time.time())
        conn.execute(
            "INSERT INTO rename_requests "
            "(id, requester_id, requester_email, collection, new_name, status, created_at, request_type, document_id, filename) "
            "VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)",
            (req_id, requester_id, requester_email, collection, new_name, created_at, request_type, document_id, filename),
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

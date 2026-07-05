import json
import os
import sqlite3
from pathlib import Path

_STORAGE_DIR = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
_DB_PATH = _STORAGE_DIR / "chat_sessions.db"
_LEGACY_JSON_PATH = _STORAGE_DIR / "chat_sessions.json"


def _connect() -> sqlite3.Connection:
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chat_sessions ("
        "id TEXT PRIMARY KEY, created_at INTEGER, data TEXT NOT NULL"
        ")"
    )
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(chat_sessions)").fetchall()}
    if "user_id" not in existing_cols:
        conn.execute("ALTER TABLE chat_sessions ADD COLUMN user_id TEXT")
    return conn


def _migrate_legacy_json_once(conn: sqlite3.Connection) -> None:
    # One-time migration from the old single-file storage (every save used to rewrite
    # the whole file). Only runs while the DB is still empty, so it's safe to call on
    # every read — it's a no-op once the migration has happened. Legacy sessions have
    # no owner, so they're left with a NULL user_id here; migrate_legacy_chat_sessions()
    # (called once at startup) backfills them to the first admin account.
    if not _LEGACY_JSON_PATH.exists():
        return
    existing = conn.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0]
    if existing > 0:
        return
    try:
        sessions = json.loads(_LEGACY_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(sessions, list):
        return
    for session in sessions:
        if not isinstance(session, dict) or "id" not in session:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO chat_sessions (id, created_at, data, user_id) VALUES (?, ?, ?, NULL)",
            (str(session["id"]), session.get("createdAt", 0), json.dumps(session, ensure_ascii=False)),
        )
    conn.commit()


def migrate_legacy_chat_sessions() -> None:
    """One-time backfill: sessions created before per-user scoping existed have no
    user_id and would otherwise become permanently invisible. Assign them to the
    first admin account, mirroring the same migration already done for memory."""
    conn = _connect()
    try:
        _migrate_legacy_json_once(conn)
        orphaned = conn.execute("SELECT COUNT(*) FROM chat_sessions WHERE user_id IS NULL").fetchone()[0]
        if orphaned == 0:
            return
        from app.infrastructure.storage.local.auth_store import list_users
        admin = next((u for u in list_users() if u["role"] == "admin"), None)
        if not admin:
            return
        conn.execute("UPDATE chat_sessions SET user_id = ? WHERE user_id IS NULL", (admin["id"],))
        conn.commit()
    finally:
        conn.close()


def load_chat_sessions(user_id: str) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT data FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [json.loads(row[0]) for row in rows]
    finally:
        conn.close()


def save_chat_sessions(sessions: list[dict], user_id: str) -> None:
    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
        for session in sessions:
            if not isinstance(session, dict) or "id" not in session:
                continue
            conn.execute(
                "INSERT INTO chat_sessions (id, created_at, data, user_id) VALUES (?, ?, ?, ?)",
                (str(session["id"]), session.get("createdAt", 0), json.dumps(session, ensure_ascii=False), user_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

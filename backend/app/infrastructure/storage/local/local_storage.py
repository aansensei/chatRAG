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
    return conn


def _migrate_legacy_json_once(conn: sqlite3.Connection) -> None:
    # One-time migration from the old single-file storage (every save used to rewrite
    # the whole file). Only runs while the DB is still empty, so it's safe to call on
    # every read — it's a no-op once the migration has happened.
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
            "INSERT OR REPLACE INTO chat_sessions (id, created_at, data) VALUES (?, ?, ?)",
            (str(session["id"]), session.get("createdAt", 0), json.dumps(session, ensure_ascii=False)),
        )
    conn.commit()


def load_chat_sessions() -> list[dict]:
    conn = _connect()
    try:
        _migrate_legacy_json_once(conn)
        rows = conn.execute("SELECT data FROM chat_sessions ORDER BY created_at DESC").fetchall()
        return [json.loads(row[0]) for row in rows]
    finally:
        conn.close()


def save_chat_sessions(sessions: list[dict]) -> None:
    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM chat_sessions")
        for session in sessions:
            if not isinstance(session, dict) or "id" not in session:
                continue
            conn.execute(
                "INSERT INTO chat_sessions (id, created_at, data) VALUES (?, ?, ?)",
                (str(session["id"]), session.get("createdAt", 0), json.dumps(session, ensure_ascii=False)),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

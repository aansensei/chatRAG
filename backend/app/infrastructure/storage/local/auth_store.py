import os
import sqlite3
import time
import uuid
from pathlib import Path

from passlib.context import CryptContext

_STORAGE_DIR = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage"))
_DB_PATH = _STORAGE_DIR / "users.db"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _connect() -> sqlite3.Connection:
    _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, "
        "role TEXT NOT NULL DEFAULT 'user', created_at INTEGER NOT NULL"
        ")"
    )
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "department" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN department TEXT")
    return conn


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_user(email: str, password: str, role: str = "user", department: str | None = None) -> dict:
    conn = _connect()
    try:
        user_id = str(uuid.uuid4())
        created_at = int(time.time())
        conn.execute(
            "INSERT INTO users (id, email, password_hash, role, created_at, department) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email.lower().strip(), hash_password(password), role, created_at, department),
        )
        conn.commit()
        return {"id": user_id, "email": email.lower().strip(), "role": role, "created_at": created_at, "department": department}
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, email, password_hash, role, created_at, department FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        if not row:
            return None
        return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3], "created_at": row[4], "department": row[5]}
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, email, role, created_at, department FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        return {"id": row[0], "email": row[1], "role": row[2], "created_at": row[3], "department": row[4]}
    finally:
        conn.close()


def list_users() -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, email, role, created_at, department FROM users ORDER BY created_at ASC"
        ).fetchall()
        return [{"id": r[0], "email": r[1], "role": r[2], "created_at": r[3], "department": r[4]} for r in rows]
    finally:
        conn.close()


def update_user(user_id: str, email: str | None = None, password: str | None = None) -> dict | None:
    conn = _connect()
    try:
        sets: list[str] = []
        params: list[str] = []
        if email is not None:
            sets.append("email = ?")
            params.append(email.lower().strip())
        if password is not None:
            sets.append("password_hash = ?")
            params.append(hash_password(password))
        if not sets:
            return get_user_by_id(user_id)
        params.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        row = conn.execute(
            "SELECT id, email, role, created_at, department FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        return {"id": row[0], "email": row[1], "role": row[2], "created_at": row[3], "department": row[4]}
    finally:
        conn.close()


def set_user_department(user_id: str, department: str | None) -> dict | None:
    conn = _connect()
    try:
        conn.execute("UPDATE users SET department = ? WHERE id = ?", (department, user_id))
        conn.commit()
        return get_user_by_id(user_id)
    finally:
        conn.close()


def delete_user(user_id: str) -> int:
    conn = _connect()
    try:
        cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def count_users() -> int:
    conn = _connect()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()

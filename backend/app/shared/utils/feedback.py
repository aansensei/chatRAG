import json
import os
import time
from pathlib import Path

_FEEDBACK_FILE = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage")) / "feedback.jsonl"


def log_feedback(user_id: str, question: str, answer: str, rating: str, model: str | None, document_ids: list[str]) -> None:
    """Append one thumbs up/down verdict as a JSON line. Never raises — feedback
    logging must not break the chat response if the write fails."""
    try:
        _FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.time(),
            "user_id": user_id,
            "question": (question or "")[:2000],
            "answer": (answer or "")[:4000],
            "rating": rating,
            "model": model or "unknown",
            "document_ids": document_ids or [],
        }
        with open(_FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_feedback() -> list[dict]:
    if not _FEEDBACK_FILE.exists():
        return []
    entries = []
    with open(_FEEDBACK_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

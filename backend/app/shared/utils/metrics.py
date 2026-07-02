import json
import os
import time
from pathlib import Path

_METRICS_FILE = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage")) / "metrics.jsonl"


def log_query_metric(model: str | None, latency_ms: int, question_len: int, success: bool, error: str | None = None) -> None:
    """Append one query's stats as a JSON line. Never raises — metrics logging
    must not break the actual request if the write fails."""
    try:
        _METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.time(),
            "model": model or "unknown",
            "latency_ms": latency_ms,
            "question_len": question_len,
            "success": success,
            "error": (error or "")[:200] or None,
        }
        with open(_METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

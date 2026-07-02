import json
import os
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter

_METRICS_FILE = Path(os.environ.get("LOCAL_STORAGE_PATH", "./storage")) / "metrics.jsonl"

router = APIRouter(prefix="/metrics", tags=["metrics"])


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

    return {
        "total_queries": total,
        "avg_latency_ms": avg_latency,
        "error_count": errors,
        "by_model": dict(by_model),
    }

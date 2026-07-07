import json
import os
import time

import redis


def _get_redis() -> redis.Redis:
    return redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True, protocol=2)


def publish(queue_name: str, message: dict) -> None:
    _get_redis().rpush(queue_name, json.dumps(message, default=str))


def set_job_status(
    job_id: str,
    status: str,
    step: str | None = None,
    error: str | None = None,
    progress: int | None = None,
) -> None:
    r = _get_redis()
    key = f"job:{job_id}"
    r.hset(key, "status", status)
    r.hset(key, "updated_at", str(time.time()))
    if step is not None:
        r.hset(key, "step", step)
    if error is not None:
        r.hset(key, "error", error)
    if progress is not None:
        r.hset(key, "progress", str(progress))


def get_job_status(job_id: str) -> dict:
    return _get_redis().hgetall(f"job:{job_id}")


def iter_jobs() -> list[tuple[str, dict]]:
    """All job_id/status pairs currently tracked in Redis — used by the
    startup sweep and the stale-job watchdog, not by request-path code."""
    r = _get_redis()
    result = []
    for key in r.keys("job:*"):
        job_id = key.split(":", 1)[1]
        result.append((job_id, r.hgetall(key)))
    return result

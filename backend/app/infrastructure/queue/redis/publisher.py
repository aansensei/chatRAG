import json
import os

import redis


def _get_redis() -> redis.Redis:
    return redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)


def publish(queue_name: str, message: dict) -> None:
    _get_redis().rpush(queue_name, json.dumps(message, default=str))


def set_job_status(job_id: str, status: str, step: str | None = None, error: str | None = None) -> None:
    mapping: dict[str, str] = {"status": status}
    if step is not None:
        mapping["step"] = step
    if error is not None:
        mapping["error"] = error
    _get_redis().hset(f"job:{job_id}", mapping=mapping)


def get_job_status(job_id: str) -> dict:
    return _get_redis().hgetall(f"job:{job_id}")

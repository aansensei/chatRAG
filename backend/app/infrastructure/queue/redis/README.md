# infrastructure/queue/redis

Tiny wrapper around `redis-py` for the ingestion pipeline. Uses plain Redis
lists (`RPUSH` + `BLPOP`) — not Redis Streams.

---

## Files

| File | Purpose |
|---|---|
| `publisher.py` | `publish(queue, msg)`, `set_job_status(...)`, `get_job_status(...)` |
| `consumer.py` | `consume(queue, handler)` blocking loop with graceful SIGTERM/SIGINT handling |

---

## Queues

| Name | Producer | Consumer |
|---|---|---|
| `queue:ocr` | `POST /ingest/upload` | `workers/ocr_worker.py` |
| `queue:chunk` | `ocr_worker` | `workers/chunk_worker.py` |
| `queue:embed` | `chunk_worker` | `workers/embedding_worker.py` |

---

## Job status

`set_job_status(job_id, status, step, progress, error)` writes a Redis hash
at `job:{job_id}` with fields:

| Field | Values |
|---|---|
| `status` | `queued`, `extracting`, `chunking`, `embedding`, `done`, `failed` |
| `step` | `ocr`, `chunk`, `embed` |
| `progress` | 0..100 |
| `error` | exception text on failure |

The frontend polls `GET /ingest/jobs/{id}` to drive the upload progress bar.

---

## Connection

```
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
```

`decode_responses=True` + `protocol=2` for compatibility with redis-py 5.

A fresh `redis.Redis` client is created per call — no pool. This is fine at
current scale; if traffic grows, add a singleton.

# infrastructure/queue

Message queue backends. Only Redis is implemented today.

| Dir | Status |
|---|---|
| `redis/` | **Active** — `RPUSH` + `BLPOP` lists, no streams |
| `kafka/` | Empty placeholder |

The `redis/` module is used by the FastAPI app (publisher) and all three
workers (consumer + status updates).

# domain/entities

Dataclasses shared across the ingestion pipeline and workers:

| Entity | File | Used by |
|---|---|---|
| `Chunk` | `chunk.py` | `text_chunker.py`, `embedding_worker.py` — carries `content`, `page_number`, `metadata` |
| `KBDocument` | `document.py` | `repository.py`, `ingest/__init__.py` |
| `IngestJob` | `ingest_job.py` | `publisher.py` job-status tracking |
| `User` | `user.py` | `auth_store.py` shape reference |
| `Review` | `review.py` | reserved — no reviewer workflow wired up yet |

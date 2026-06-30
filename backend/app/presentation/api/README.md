# presentation/api

FastAPI routers. Mounted in `main.py`.

| Folder | Prefix | Status | Notes |
|---|---|---|---|
| `chat/` | `/chat` | **Active** | RAG endpoint + suggestions |
| `ingest/` | `/ingest` | **Active** | Upload, KB management, file viewer |
| `auth/` | none | **Active** (utility) | `get_collections` dependency for API-key -> folder list |
| `admin/` | — | Empty | planned |
| `chunks/` | — | Empty | planned (debug view of chunks) |
| `documents/` | — | Empty | replaced by `/ingest/documents` |
| `jobs/` | — | Empty | replaced by `/ingest/jobs/{id}` |
| `metrics/` | — | Empty | Prometheus scraping planned |
| `reviews/` | — | Empty | human-review workflow planned |

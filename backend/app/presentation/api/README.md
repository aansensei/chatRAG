## presentation/api

FastAPI APIRouters grouped by resource. Each subfolder is one router with its own prefix, included in `main.py`.

### Subdirectories

`admin/` - admin-only endpoints (prefix: `/admin`), guarded by UserRole.ADMIN

`auth/` - login, logout, token refresh (prefix: `/auth`)

`chat/` - RAG query endpoint (prefix: `/chat`)

`chunks/` - view chunks for a document, useful for debugging retrieval (prefix: `/chunks`)

`documents/` - upload, list, get, delete documents (prefix: `/documents`)

`jobs/` - ingest job status polling (prefix: `/jobs`)

`metrics/` - Prometheus metrics scraping endpoint (prefix: `/metrics`)

`reviews/` - review queue for sensitive documents (prefix: `/reviews`)

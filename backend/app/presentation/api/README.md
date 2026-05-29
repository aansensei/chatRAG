## presentation/api

FastAPI APIRouters grouped theo resource. Mỗi subfolder là một router với prefix riêng, được include vào app ở `main.py`.

### Subdirectories

`admin/` - admin-only endpoints (prefix: `/admin`), protected bằng UserRole.ADMIN

`auth/` - login, logout, token refresh (prefix: `/auth`)

`chat/` - RAG query endpoint (prefix: `/chat`)

`chunks/` - xem chunks của một document, debugging retrieval (prefix: `/chunks`)

`documents/` - upload, list, get, delete documents (prefix: `/documents`)

`jobs/` - ingest job status polling (prefix: `/jobs`)

`metrics/` - Prometheus metrics scraping endpoint (prefix: `/metrics`)

`reviews/` - review queue cho sensitive documents (prefix: `/reviews`)

# app

Root of the Python application. Organized as Clean Architecture but most
inner layers are placeholders today — the working code lives in
`application/retrieval`, `infrastructure/vector/supabase`,
`infrastructure/queue/redis`, `presentation/api/chat|ingest|auth`,
and `shared/utils`.

```
domain         pure business rules — placeholder, no code
application    use cases — only retrieval is implemented
infrastructure concrete implementations — supabase + redis are live
presentation   HTTP layer — FastAPI routers
shared         cross-cutting utilities — embedders, extractors, chunkers
```

Imports flow inward: `presentation` -> `application` -> `domain`.
`infrastructure` is imported by `application` (which is a deliberate
violation of strict clean architecture, accepted for simplicity at this
project's size).

---

## What's implemented

| Path | Status |
|---|---|
| `application/retrieval/ask_question.py` | RAG pipeline |
| `infrastructure/vector/supabase/repository.py` | pgvector + ilike queries |
| `infrastructure/queue/redis/{publisher,consumer}.py` | Redis lists |
| `presentation/api/chat/` | POST /chat (SSE) |
| `presentation/api/ingest/` | Upload + KB management |
| `presentation/api/auth/` | API-key -> allowed collections |
| `shared/utils/extractors/` | PDF, DOCX, XLSX, CSV, OCR |
| `shared/utils/embedders/` | sentence-transformers |
| `shared/utils/chunkers/` | paragraph-aware split |

Everything else (domain/, application/{auth,ingestion,jobs,permission,review},
infrastructure/{classifier,database,embedding,llm,ocr,parser,storage},
presentation/{api/admin,api/auth,api/chunks,api/documents,api/jobs,
api/metrics,api/reviews,middleware,websocket}) is an **empty scaffold**.
The folders exist so we don't have to invent structure when we add those
features later.

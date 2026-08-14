# chatRAG — Backend

FastAPI server for **Ciel**, the chatRAG assistant. Handles file upload, OCR/chunk/embed pipeline, retrieval, and SSE streaming.

---

## Quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

In another terminal:

```bash
python -m workers.ocr_worker
```

- API: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- Static UI (after `pnpm build` in `../frontend`): `http://localhost:8000`
- Default login (seeded on first run): `admin@aanjsc.vn` / `000000` — change after logging in.

---

## Architecture

```
                       +------------------------+
   POST /chat (SSE) -->|  ask_question.stream_ask|
                       +-----------+------------+
                                   |
   Auth gate (JWT, app/presentation/api/auth) -> department-scoped
   collection filter (app/shared/security/permissions.py)
                                   |
   Intercepts (no retrieval):      v
     - wake-up        ("ciel ơi")  identity / help / RAG-explainer
     - identity       ("bạn là ai") prompts go straight to LLM
     - rag-explainer  ("rag là j")
                                   |
   Otherwise:                      v
     1. query rewriting (follow-up resolved against history)
     2. embed question (multilingual-e5-base / BGE-M3), HyDE + multi-query expansion
     3. filename_search_chunks   (Supabase metadata->>source ilike)
        - tries longest token first; stops at first hit
        - strong tokens (Cam7, 14_BangLuong_T12_2025) trigger
          "file not found" early-return when no match
        - skips tokens that match >3 distinct documents (too generic to trust)
     4. search_chunks            (hybrid: BM25 + pgvector cosine, RRF fusion)
     5. keyword_search_chunks    (ilike fallback for codes / IDs)
     6. tabular-aware: chunks with "  |  " separator skip reranker/LLM filter
     7. _bge_rerank cross-encoder + fetch_context_windows (parent-child expansion)
     8. GraphRAG block (_format_graph_block — supplementary context only, not
        fused into ranking)
     9. _llm_filter_chunks       (LLM judges relevance, drops noise)
     10. directive or general system prompt -> _stream_llm (Ollama / Groq)
     11. query + sources + latency logged to storage/metrics.jsonl for the
         admin audit dashboard (GET /metrics/audit)


   POST /ingest/upload --> writes file --> publish("queue:ocr")
                                                |
                                                v
                              workers/ocr_worker.py
                                  (extract text -> chunk -> embed -> Supabase)
```

---

## Directory layout

```
backend/
  main.py                            FastAPI entrypoint, mounts routers, spawns workers, serves /static
  app/
    application/
      retrieval/
        ask_question.py              stream_ask() — full RAG pipeline + Ciel intercepts
    domain/
      entities/                      Chunk, KBDocument, IngestJob, User, Review — dataclasses
                                     used across workers/chunkers/embedder
    infrastructure/
      vector/supabase/
        repository.py                list_collections, list_documents,
                                     filename_search_chunks, keyword_search_chunks,
                                     search_chunks, upsert_chunks, delete_document
      queue/redis/
        publisher.py                 publish, set_job_status, get_job_status, iter_jobs
      storage/local/
        auth_store.py                SQLite users.db — create/update/delete user, password hashing
        local_storage.py             SQLite chat_sessions.db — chat history persistence
    presentation/
      middleware/
        rate_limit.py                per-IP sliding-window rate limit on /chat /ingest /memory /auth
      api/
        chat/__init__.py             POST /chat, GET /chat/suggestions
        ingest/__init__.py           POST /ingest/upload, GET /ingest/documents,
                                     GET /ingest/documents/{id}/file (inline PDF, etc.)
        auth/__init__.py             POST /auth/login, GET/PATCH /auth/me, admin user management
        memory/__init__.py           GET/POST/DELETE /memory — saved-notes-style persistent memory
        metrics/__init__.py          GET /metrics/summary, GET /metrics/audit (admin only)
    shared/
      security/permissions.py        is_admin_or_leadership, can_read_collection (department ACL)
      utils/
        embedders/text_embedder.py   sentence-transformers wrapper
        extractors/                  pdf, docx, xlsx, csv, ocr, dispatcher
  workers/
    ocr_worker.py / chunk_worker.py / embedding_worker.py
                                     3-stage pipeline: OCR+extract -> chunk -> embed + write
  scripts/
    eval_retrieval.py                golden-set retrieval quality eval, wired into CI
  storage/                           uploaded files, SQLite DBs, logs (gitignored)
  app/static/                        production frontend build
```

Other folders (`app/application/{auth,ingestion,jobs,permission,review}`,
`app/domain/{events,repositories}`,
`app/infrastructure/{classifier,database,embedding,llm,ocr,parser}`,
`app/infrastructure/{queue/kafka,storage/minio,vector/milvus,vector/qdrant}`,
`app/presentation/{websocket,api/admin,api/chunks,api/documents,api/jobs,api/reviews}`,
`consumers/`, `scheduler/`, `monitoring/`, `docker/`)
are clean-architecture scaffolding kept for future expansion — every file in
them is empty. They do not contain working code today. (Candidates for
removal if they stay unused — see project notes.)

---

## Environment variables

| Var | Purpose | Default |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | required |
| `SUPABASE_SERVICE_KEY` | Service role key | required |
| `REDIS_URL` | Redis connection | required |
| `LOCAL_STORAGE_PATH` | Upload directory | `./storage` |
| `OLLAMA_BASE_URL` | Ollama server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Default model | `gemma3:4b` |
| `RETRIEVAL_TOP_K` | Vector top-k | `8` |
| `MAX_CHUNK_CHARS` | Chars per chunk in prompt | `1200` |
| `DEV_MODE` | Skip API-key auth | `true` |
| `API_KEYS` | JSON `{key: [collections]}` for non-dev | `""` |
| `JWT_SECRET_KEY` | Signs login tokens | required |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `1440` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | First-run bootstrap admin (only used when `users.db` is empty) | `admin@aanjsc.vn` / `000000` |
| `EMBEDDING_DEVICE` | Forces the main process's embedder onto this device; NOT inherited by spawned workers (always GPU) | unset |
| `RATE_LIMIT_PER_MINUTE` | Per-IP request budget on rate-limited routes | `30` |
| `MAX_UPLOAD_MB` | Reject uploads above this size (413) before the body is parsed | `50` |

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Ask question, SSE stream tokens + sources |
| GET | `/chat/suggestions` | Starter prompts based on KB content |
| POST | `/ingest/upload` | Upload file, queue OCR/chunk/embed |
| GET | `/ingest/jobs/{id}` | Poll job status |
| GET | `/ingest/documents` | List docs in user's collections |
| DELETE | `/ingest/documents/{id}` | Delete doc + its chunks |
| GET | `/ingest/documents/{id}/file` | Serve original file (inline for PDF/img/csv) |
| GET | `/ingest/collections` | List folders with doc counts |
| PATCH | `/ingest/collections/{name}` | Rename folder |
| DELETE | `/ingest/collections/{name}` | Delete folder + all its docs |
| POST | `/auth/login` | Email + password -> JWT |
| GET / PATCH | `/auth/me` | Current user profile / self-service email+password update |
| GET / POST | `/auth/users` | Admin: list / create users |
| PATCH | `/auth/users/{id}/expiry` \| `/department` \| `/department-head` | Admin: edit a user |
| DELETE | `/auth/users/{id}` | Admin: remove a user |
| GET / POST / DELETE | `/memory` | Persistent notes-style memory (per user) |
| GET | `/metrics/summary` | Admin: query volume, latency, error rate by model/user |
| GET | `/metrics/audit` | Admin: query-level audit log (who asked what, when) |
| PATCH | `/ingest/documents/{id}/collection` | Move doc to another folder |

---

## Ciel intercepts (in `ask_question.py`)

These short-circuit retrieval entirely:

| Trigger | Behavior |
|---|---|
| `ciel ơi`, `hey ciel`, `シエルさん` | Random greeting, no LLM tokens streamed (typewriter) |
| `bạn là ai`, `who are you`, `/help`, `ciel có thể tạo ảnh không` | Identity prompt -> LLM with strong persona |
| `rag là gì`, `what is rag`, `chatrag là gì` | RAG-explainer prompt -> LLM |

Everything else goes through the retrieval pipeline.

---

## Supported file types

`.pdf` `.docx` `.xlsx` `.csv` `.png` `.jpg` `.jpeg` `.tiff` `.bmp`

CSV files are tried in UTF-8-SIG / UTF-8 / CP1258 / CP1252 / Latin-1 order
to handle Windows Excel exports cleanly.

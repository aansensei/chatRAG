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

---

## Architecture

```
                       +------------------------+
   POST /chat (SSE) -->|  ask_question.stream_ask|
                       +-----------+------------+
                                   |
   Intercepts (no retrieval):      v
     - wake-up        ("ciel ơi")  identity / help / RAG-explainer
     - identity       ("bạn là ai") prompts go straight to LLM
     - rag-explainer  ("rag là j")
                                   |
   Otherwise:                      v
     1. embed question (multilingual-e5-base)
     2. filename_search_chunks   (Supabase metadata->>source ilike)
        - tries longest token first; stops at first hit
        - strong tokens (Cam7, 14_BangLuong_T12_2025) trigger
          "file not found" early-return when no match
     3. search_chunks            (pgvector cosine)
     4. keyword_search_chunks    (ilike fallback for codes / IDs)
     5. tabular-aware: chunks with "  |  " separator skip LLM filter
     6. _llm_filter_chunks       (LLM judges relevance, drops noise)
     7. directive or general system prompt -> _stream_llm (Ollama / Groq)


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
  main.py                            FastAPI entrypoint, mounts /chat /ingest, serves /static
  app/
    application/
      retrieval/
        ask_question.py              stream_ask() — full RAG pipeline + Ciel intercepts
    infrastructure/
      vector/supabase/
        repository.py                list_collections, list_documents,
                                     filename_search_chunks, keyword_search_chunks,
                                     search_chunks, upsert_chunks
      queue/redis/
        publisher.py                 publish, set_job_status, get_job_status
    presentation/
      api/
        chat/__init__.py             POST /chat, GET /chat/suggestions
        ingest/__init__.py           POST /ingest/upload, GET /ingest/documents,
                                     GET /ingest/documents/{id}/file (inline PDF, etc.)
        auth/__init__.py             API key -> allowed collections (dev mode bypass)
    shared/
      utils/
        embedders/text_embedder.py   sentence-transformers wrapper
        extractors/                  pdf, docx, xlsx, csv, ocr, dispatcher
  workers/
    ocr_worker.py                    main worker: OCR + extract + chunk + embed + write
  storage/                           uploaded files (gitignored)
  app/static/                        production frontend build
```

Other folders (`app/domain`, `app/application/auth|jobs|permission|review`,
`app/infrastructure/{classifier,database,embedding,llm,ocr,parser,storage}`,
`app/presentation/api/{admin,auth,chunks,documents,jobs,metrics,reviews}`,
`consumers/`, `scheduler/`, `monitoring/`, `docker/`, `tests/`)
are clean-architecture placeholders kept for future expansion. They do not
contain working code today.

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

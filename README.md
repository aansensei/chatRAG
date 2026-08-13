# chatRAG

Retrieval-Augmented Generation chatbot named **Ciel** — built as an internal AI assistant for SADEC Technology. Upload company documents, ask in natural language, get answers grounded in your files with inline citations.

Developed during internship at **SADEC Technology JSC**.

---

## What it does

- Upload PDF, Word, Excel, CSV, images (with OCR) into named folders
- Ask in Vietnamese, English, or Japanese
- Get answers cited back to the source document with inline `[N]` clickable citations
- Multi-turn chat with conversation memory and **query rewriting** (follow-up questions resolved against history before embedding)
- Hybrid mode: blend internal docs with general knowledge when KB is empty
- Strict context-only answers — will not hallucinate names, figures, or project names outside the uploaded documents
- Run locally with Ollama or fast via Groq cloud (Llama 3.3 / Gemma 2 / etc.)
- Model availability detection: UI shows ⚠ "Not installed" badge for Ollama models not yet pulled

---

## Repository layout

```
chatRAG/
  backend/    FastAPI server + retrieval engine + Redis workers
  frontend/   React + Vite chat UI (built into backend/app/static for serving)
  start.ps1   One-command dev bootstrap (Windows PowerShell)
  start.bat   One-command dev bootstrap (Windows CMD)
  stop.ps1    Stop backend/worker/frontend processes, optionally stop Ollama (frees GPU/RAM)
```

---

## Architecture

```
React UI (frontend/)
    |
    | POST /chat (SSE stream)
    v
FastAPI (backend/)
    |
    |-- JWT auth gate -> department-scoped collection filter
    |
    |-- Identity / wake-up / RAG-explainer  short-circuits  -> LLM
    |
    |-- Normal query:
    |     1. query rewriting        (follow-up resolved via history before embedding)
    |     2. HyDE + multi-query expansion, embed with multilingual-e5-base (BGE-M3)
    |     3. filename-aware search        (exact file match via metadata->source)
    |     4. hybrid search                (BM25 + pgvector cosine, RRF fusion)
    |     5. keyword fallback              (ilike for codes, IDs, VI diacritic-stripped)
    |     6. table-aware bypass            (skip reranker/LLM filter for tabular chunks)
    |     7. BGE cross-encoder reranking + parent-child context window expansion
    |     8. GraphRAG block (supplementary context, not yet fused into ranking)
    |     9. LLM relevance filter          (drops noise)
    |     10. directive or strict-context prompt -> LLM stream, citations track source page
    |
    |-- Upload pipeline:
          file -> Redis queue -> OCR worker -> chunker -> embedder -> Supabase
          (stale versions of the same filename are deleted on re-upload)
```

---

## Tech stack

| Layer | Tech |
|---|---|
| API | FastAPI, SSE streaming |
| Vector DB | Supabase (Postgres + pgvector) |
| Queue | Redis pub/sub |
| OCR | PaddleOCR, python-docx, openpyxl, csv (multi-encoding: utf-8-sig → cp1258 → latin-1) |
| Embedding | `intfloat/multilingual-e5-base` via sentence-transformers |
| LLM | Ollama (local, default `gemma3:4b`) or cloud: Groq, OpenAI, Gemini, OpenRouter, Cerebras, Anthropic — server-side key or per-request key from the UI |
| Frontend | React 18, Vite, TypeScript, Tailwind |

---

## Quick start

### Option A — One command (PowerShell)

```powershell
.\start.ps1
```

Opens two terminal windows: backend on `:8000`, frontend on `:5173`.

### Option B — Manual

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill SUPABASE_URL, SUPABASE_SERVICE_KEY, REDIS_URL, JWT_SECRET_KEY
uvicorn main:app --reload
```

`uvicorn main:app` auto-spawns the OCR/chunk/embedding workers as subprocesses
(with a watchdog that restarts them if they crash or stall). To run a worker
standalone instead:

```bash
cd backend
python -m workers.ocr_worker
```

API: `http://localhost:8000`  /  Docs: `http://localhost:8000/docs`

**Frontend (dev mode):**

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:5173 (proxies /chat, /ingest to :8000)
```

**Frontend (production deploy):**

```bash
cd frontend
pnpm run build:deploy
# Builds and copies dist/* into ../backend/app/static — served by FastAPI at :8000
```

---

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | required |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | required |
| `REDIS_URL` | Redis connection | required |
| `LOCAL_STORAGE_PATH` | Where uploaded files live | `./storage` |
| `OLLAMA_BASE_URL` | Ollama host | `http://localhost:11434` |
| `OLLAMA_MODEL` | Default Ollama model | `gemma3:4b` |
| `RETRIEVAL_TOP_K` | Chunks per query | `8` |
| `MAX_CHUNK_CHARS` | Chars per chunk in prompt | `1200` |
| `JWT_SECRET_KEY` | Signs login tokens | required |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | First-run bootstrap admin account | `admin@aanjsc.vn` / none |
| `GROQ_API_KEY` | Server-side Groq key (optional; UI can also send a per-request key) | `""` |
| `EMBEDDING_DEVICE` | Force the main process's embedder onto `cpu`/`cuda` (workers ignore this, always GPU) | unset (auto) |
| `RATE_LIMIT_PER_MINUTE` | Per-IP request budget on `/chat`, `/ingest`, `/memory`, `/auth` | `30` |

---

## Supported file types

`.pdf` `.docx` `.xlsx` `.csv` `.png` `.jpg` `.jpeg` `.tiff` `.bmp`

---

## Retrieval features

| Feature | Notes |
|---|---|
| Filename-aware retrieval | Longest-token-first; strong identifiers trigger early return if file not found |
| Vietnamese keyword → filename mapping | `lương` → BangLuong, `dự án` → DuAn, etc. |
| Diacritic-stripped fallback | Searches both `lương` and `luong` |
| Tabular-aware retrieval | Chunks with `  \|  ` skip LLM filter and use directive prompt |
| LLM relevance filter | Groq or Ollama judges chunk relevance before generating |
| Query rewriting | Follow-up questions rewritten as standalone before embedding |

---

## Status

| Feature | State |
|---|---|
| Multi-folder knowledge base | ✅ done |
| Filename-aware + hybrid (BM25+vector) + keyword retrieval | ✅ done |
| Table / CSV / XLSX-aware retrieval | ✅ done |
| Multi-turn chat memory (history inject + persisted across reloads) | ✅ done |
| Query rewriting, HyDE, multi-query expansion | ✅ done |
| BGE cross-encoder reranking | ✅ done |
| GraphRAG context block (supplementary — not yet fused into ranking) | partial |
| Strict context-only answers (no hallucination) | ✅ done |
| Inline citations `[N]`, click jumps to exact page in source PDF | ✅ done |
| Ciel persona (VI / EN / JA) | ✅ done |
| Hybrid mode (KB + general knowledge) | ✅ done |
| Source citations + file viewer (PDF inline / DOCX download) | ✅ done |
| CSV upload with multi-encoding support | ✅ done |
| Ollama model availability detection | ✅ done |
| Effort selector (fast / medium / reasoning) | ✅ done |
| Stale document cleanup on re-upload | ✅ done |
| Retrieval quality eval wired into CI (nightly + manual) | ✅ done |
| JWT auth, per-department folder permissions, admin user management | ✅ done |
| Query-level audit log (admin dashboard) | ✅ done |
| build:deploy script (vite build → static/) | ✅ done |
| start.ps1 / stop.ps1 one-command bootstrap | ✅ done |
| Login rate-limiting | ✅ done |
| Admin-action audit trail (who edited/deleted which user account) | ✅ done |
| Upload size cap (413 before oversized files hit disk) | ✅ done |
| Security response headers (nosniff, deny-framing, referrer-policy) | ✅ done |
| Image / vision input | planned |
| Multi-tenant (multiple separate companies on one deployment) | planned |
| Self-service password reset, bulk user import, session/device visibility | planned |

---

## License

MIT — see [LICENSE](LICENSE).

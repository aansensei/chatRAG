# workers

Long-running background processes that handle the document ingestion pipeline.
Each worker reads from a Redis queue (`BLPOP`) and pushes the next stage onto
the next queue.

`main.py` spawns all three as subprocesses on FastAPI startup and restarts
them via a watchdog thread if they crash.

---

## Pipeline

```
POST /ingest/upload
    |
    | publish queue:ocr
    v
ocr_worker.py          extract text (PDF/OCR/DOCX/XLSX/CSV/image)
    | publish queue:chunk
    v
chunk_worker.py        paragraph-aware split into chunks
    | publish queue:embed
    v
embedding_worker.py    embed each chunk -> Supabase upsert
```

Job progress is tracked in Redis (`job:{id}` hash) via `set_job_status`
so the frontend can poll `GET /ingest/jobs/{id}`.

---

## Files

| Worker | Reads | Writes | Notes |
|---|---|---|---|
| `ocr_worker.py` | `queue:ocr` | `queue:chunk` | Routes by extension: PDF -> OCR, DOCX -> python-docx, XLSX -> openpyxl, CSV -> multi-encoding csv, image -> PaddleOCR |
| `chunk_worker.py` | `queue:chunk` | `queue:embed` | Paragraph-aware splitter (`app/shared/utils/chunkers`) |
| `embedding_worker.py` | `queue:embed` | Supabase `chunks` table | Uses `multilingual-e5-base` via sentence-transformers |

---

## Running manually

Workers auto-start when `uvicorn main:app` runs. To run independently:

```bash
python -m workers.ocr_worker
python -m workers.chunk_worker
python -m workers.embedding_worker
```

Stop uvicorn cleanly (Ctrl+C, not kill -9) so the lifespan shutdown can
terminate the child workers. Force-killing uvicorn leaves orphan workers
holding the Redis BLPOP connection.

---

## CSV encoding

`extract_csv` in `office_extractor.py` tries encodings in this order:
`utf-8-sig` -> `utf-8` -> `cp1258` -> `cp1252` -> `latin-1`.
This handles Windows Excel exports that often use cp1258 for Vietnamese.

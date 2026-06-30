# infrastructure/vector/supabase

Supabase (Postgres + pgvector) repository. Single module: `repository.py`.

---

## Schema

One table: `chunks`.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `document_id` | uuid | Groups chunks of one source file |
| `chunk_index` | int | Order within document |
| `content` | text | Chunk text |
| `section_title` | text | Heading, if detected |
| `token_count` | int | For budgeting |
| `metadata` | jsonb | `{source, file_path, pages, ...}` |
| `embedding` | vector(768) | `multilingual-e5-base` output |
| `collection` | text | Folder name (or `"default"`) |

An RPC `match_chunks(query_embedding, match_threshold, match_count, filter_collections)`
performs the cosine search and returns rows with a `similarity` score.

---

## Functions

| Function | Used by |
|---|---|
| `upsert_chunks(rows)` | `embedding_worker` |
| `search_chunks(vector, k=15, threshold=0.3, collections=None)` | `ask_question.stream_ask` |
| `keyword_search_chunks(keywords, k=6, collections=None)` | `ask_question.stream_ask` (ilike fallback) |
| `filename_search_chunks(tokens, collections=None)` | `ask_question.stream_ask` (filename-aware) |
| `list_collections()` | `GET /ingest/collections` |
| `list_documents(collections=None)` | `GET /ingest/documents`, `GET /chat/suggestions` |
| `get_document_file_path(id)` | `GET /ingest/documents/{id}/file` |
| `delete_document(id)` | `DELETE /ingest/documents/{id}` |
| `delete_collection_docs(name)` | `DELETE /ingest/collections/{name}` |
| `rename_collection(old, new)` | `PATCH /ingest/collections/{name}` |
| `move_document_collection(doc, new)` | `PATCH /ingest/documents/{id}/collection` |

---

## Key behaviors

- `list_collections` and `list_documents` use `.limit(10000)` to avoid the
  Supabase default ~100-row cap. Without this, large KBs miss folders / docs.
- `filename_search_chunks` tries tokens from longest to shortest and returns
  on the first hit. This means `Cam7 test 2 writing task 2` is preferred
  over the broader `Cam7`, so only the specific file is returned.
- `search_chunks` post-expands every hit: for chunks with a `section_title`,
  all sibling chunks in the same section are loaded; otherwise the next
  5 chunks by index are loaded. This gives the LLM coherent context blocks
  instead of orphan paragraphs.
- Embeddings are vector(768) — change `multilingual-e5-base` -> something
  else and you need to re-create the table and re-embed.

---

## Connection

```python
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
```

The client is created fresh per call (`_get_client()`). No connection pool —
Supabase's HTTPS API handles concurrency.

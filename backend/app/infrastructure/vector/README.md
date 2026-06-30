# infrastructure/vector

Vector store implementations. Currently only Supabase (Postgres + pgvector)
is wired up. The `qdrant/` and `milvus/` directories are scaffolding for
possible future swaps and contain no working code.

---

## Subdirectories

| Dir | Status |
|---|---|
| `supabase/` | **Active** — pgvector + ilike queries |
| `qdrant/` | Empty placeholder |
| `milvus/` | Empty placeholder |

---

## Supabase API surface

See `supabase/README.md`. The main functions:

| Function | Purpose |
|---|---|
| `upsert_chunks(rows)` | Write chunks + embeddings (worker) |
| `search_chunks(vector, k, threshold, collections)` | pgvector cosine search via `match_chunks` RPC. Auto-expands hits to neighbors in the same section. |
| `keyword_search_chunks(keywords, k, collections)` | ilike fallback for codes, IDs |
| `filename_search_chunks(tokens, collections)` | Match `metadata->>source` for filename-aware retrieval |
| `list_collections()` | All folders with doc counts |
| `list_documents(collections)` | All docs in given folders |
| `get_document_file_path(id)` | Local file path for viewer endpoint |
| `delete_document(id)`, `delete_collection_docs(name)` | Cleanup |
| `rename_collection(old, new)`, `move_document_collection(doc, new)` | KB management |

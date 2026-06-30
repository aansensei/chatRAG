# infrastructure

Concrete adapters for external systems. Most folders are placeholders —
the live integrations are inlined where they're used.

| Folder | Status | What actually lives there / where |
|---|---|---|
| `vector/supabase/` | **Active** | pgvector queries used by retrieval |
| `queue/redis/` | **Active** | RPUSH/BLPOP wrapper used by /ingest + workers |
| `vector/qdrant/`, `vector/milvus/` | Empty | scaffolding for future swap |
| `queue/kafka/` | Empty | scaffolding for future swap |
| `storage/local/` | Empty (logic is in `presentation/api/ingest`) | files written to `LOCAL_STORAGE_PATH` |
| `storage/minio/` | Empty | planned for prod |
| `embedding/` | Empty (logic in `shared/utils/embedders/text_embedder.py`) | |
| `llm/` | Empty (logic in `application/retrieval/ask_question.py`) | Ollama + Groq calls inlined there |
| `ocr/` | Empty (logic in `shared/utils/extractors/ocr_extractor.py`) | PaddleOCR |
| `parser/` | Empty (logic in `shared/utils/extractors/`) | |
| `classifier/` | Empty | document sensitivity labeling — planned |
| `database/` | Empty | Supabase is queried directly via REST, no SQLAlchemy |

This violates a strict reading of clean architecture (some "infrastructure"
lives in `shared/utils`), but it keeps the wiring obvious at small scale.
When a folder gets real code, move logic into it and adjust callers.

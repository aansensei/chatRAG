# shared/utils

Domain-agnostic helpers used by the API, workers, and retrieval.

| Folder | Purpose |
|---|---|
| `extractors/` | Read text from `.pdf` / `.docx` / `.xlsx` / `.csv` / `.pptx` / images. Dispatcher picks the right one by extension. |
| `chunkers/` | Paragraph-aware splitter — `chunk_text(text, document_id, ChunkConfig())`. Tries to keep paragraphs whole; falls back to sentence boundaries when too long. |
| `embedders/` | `text_embedder.py` wraps `sentence-transformers` (multilingual-e5-base). Exposes `embed_text(str) -> list[float]` and `embed_chunks([Chunk]) -> list[list[float]]`. |

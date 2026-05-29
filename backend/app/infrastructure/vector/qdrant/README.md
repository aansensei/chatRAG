## infrastructure/vector/qdrant

Qdrant vector DB implementation.

### Files

`repository.py` - implements `VectorRepository`: upsert embedding vectors với payload (chunk_id, document_id), similarity search theo query vector với filter theo document hoặc sensitivity, xóa toàn bộ vectors của một document.

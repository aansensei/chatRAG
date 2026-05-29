## infrastructure/vector/qdrant

Qdrant vector DB implementation.

### Files

`repository.py` - implements `VectorRepository`: upsert embedding vectors with payload (chunk_id, document_id), similarity search by query vector with optional filter by document or sensitivity, delete all vectors for a given document.

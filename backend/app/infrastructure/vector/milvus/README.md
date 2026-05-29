## infrastructure/vector/milvus

Milvus vector DB implementation. Cùng interface với Qdrant, dùng khi cần horizontal scaling hoặc đã có Milvus cluster sẵn.

### Files

`repository.py` - implements `VectorRepository` với Milvus Python SDK.

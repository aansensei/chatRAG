## infrastructure/vector/milvus

Milvus vector DB implementation. Same interface as Qdrant, used when horizontal scaling is needed or a Milvus cluster is already available.

### Files

`repository.py` - implements `VectorRepository` using the Milvus Python SDK.

## infrastructure/vector

Vector database implementations. Qdrant cho local/dev (Docker, dễ setup), Milvus như alternative khi cần scale lớn hơn.

Cả hai implement interface từ `domain/repositories/vector_repo.py`. Khi đổi vector DB, chỉ cần swap implementation ở DI config.

### Subdirectories

`qdrant/` - Qdrant implementation (default cho dev)

`milvus/` - Milvus implementation (alternative cho production scale)

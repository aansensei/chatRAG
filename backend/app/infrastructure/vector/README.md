## infrastructure/vector

Vector database implementations. Qdrant for local/dev (Docker, easy to set up), Milvus as an alternative when larger scale is needed.

Both implement the interface from `domain/repositories/vector_repo.py`. Switching the vector DB only requires changing the DI binding.

### Subdirectories

`qdrant/` - Qdrant implementation (default for dev)

`milvus/` - Milvus implementation (alternative for production scale)

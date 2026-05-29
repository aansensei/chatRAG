## domain/repositories

Abstract interfaces (Protocol or ABC) for data access. The application layer depends on these interfaces, not on concrete implementations. Infrastructure implements them.

This makes it possible to swap the database or queue without touching application logic — switching from Qdrant to Milvus only requires a new implementation of `vector_repo.py`.

### Files

`document_repo.py` - CRUD for Document (save, get by id, list, update status).

`user_repo.py` - CRUD for User, lookup by email.

`ingest_job_repo.py` - CRUD for IngestJob, query by document_id and status.

`review_repo.py` - CRUD for Review, query pending reviews.

`vector_repo.py` - interface for vector DB: upsert embeddings, similarity search, delete by document.

`queue_repo.py` - interface for publishing domain events to the message queue (Kafka or Redis).

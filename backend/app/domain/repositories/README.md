## domain/repositories

Abstract interfaces (Protocol hoặc ABC) cho data access. Application layer phụ thuộc vào những interfaces này, không phụ thuộc vào implementation cụ thể. Infrastructure implement chúng.

Giúp swap DB hoặc queue mà không sửa application logic - ví dụ đổi từ Qdrant sang Milvus chỉ cần implement `vector_repo.py` với adapter mới.

### Files

`document_repo.py` - CRUD cho Document entity (lưu, lấy theo id, list, update status).

`user_repo.py` - CRUD cho User, lookup theo email.

`ingest_job_repo.py` - CRUD cho IngestJob, query theo document_id và status.

`review_repo.py` - CRUD cho Review, query pending reviews.

`vector_repo.py` - interface cho vector DB: upsert embeddings, similarity search, delete by document.

`queue_repo.py` - interface publish domain events ra message queue (Kafka hoặc Redis).

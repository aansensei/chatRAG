## infrastructure

Concrete implementations of domain repository interfaces. This layer is free to import any third-party library (SQLAlchemy, httpx, boto3, ...). The application layer never imports from here directly.

All implementations are pluggable: swap Kafka → Redis, Qdrant → Milvus, or local storage → MinIO without touching application logic.

### Subdirectories

`classifier/` - ML model for assigning sensitivity labels

`database/` - PostgreSQL + Alembic migrations

`embedding/` - embedding model for vectorizing text

`llm/` - LLM client (Ollama)

`ocr/` - OCR engine (PaddleOCR)

`parser/` - document structure parser (Unstructured.io)

`queue/` - message queue (Kafka / Redis Streams)

`storage/` - file storage (local / MinIO)

`vector/` - vector database (Qdrant / Milvus)

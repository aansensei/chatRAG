## infrastructure

Concrete implementations của các interfaces từ domain/repositories. Layer này được phép import bất kỳ thư viện nào (SQLAlchemy, httpx, boto3, ...). Application layer không import từ đây trực tiếp.

Tất cả các implementation đều pluggable: swap Kafka → Redis, Qdrant → Milvus, local storage → MinIO mà không đụng application logic.

### Subdirectories

`classifier/` - ML model để assign sensitivity label

`database/` - PostgreSQL + Alembic migrations

`embedding/` - embedding model để vector hóa text

`llm/` - LLM client (Ollama)

`ocr/` - OCR engine (PaddleOCR)

`parser/` - document structure parser (Unstructured.io)

`queue/` - message queue (Kafka / Redis Streams)

`storage/` - file storage (local / MinIO)

`vector/` - vector database (Qdrant / Milvus)

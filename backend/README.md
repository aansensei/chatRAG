# chatRAG: Backend

FastAPI backend for the chatRAG platform. Handles document ingestion, asynchronous pipeline processing, role-based retrieval, and LLM streaming.

For project-wide setup, deployment, and frontend documentation see the root `README.md`.

---

## Table of Contents

* Architectural Design
* Asynchronous Data Pipeline
* Technology Stack
* Directory Structure
* Local Setup
* Environment Variables
* Running Workers
* Operational Notes

---

## Architectural Design

### Clean Architecture

The backend is organized into four dependency layers. Each layer may only depend on layers interior to it.

**Domain** is the innermost layer. It contains entities, enums, domain events, and repository interfaces. It has zero external dependencies and no imports from any framework or infrastructure library. Business rules defined here are stable and independently testable.

**Application** contains use case implementations that orchestrate domain entities and repository interfaces. Use cases cover ingestion initiation, review approval, retrieval queries, permission validation, and job status reporting. This layer has no knowledge of FastAPI, SQLAlchemy, or any specific infrastructure provider.

**Infrastructure** contains concrete implementations of domain repository interfaces. This includes PostgreSQL access via SQLAlchemy, vector operations via Qdrant, queue publishing and consumption via Redis and Celery, file storage via local filesystem or MinIO, OCR via PaddleOCR, parsing via Unstructured, embedding inference, sensitivity classification, and LLM communication. Swapping any provider requires only replacing the relevant file in this layer.

**Presentation** is the outermost layer. It contains FastAPI route definitions, Pydantic schemas, WebSocket handlers for chat streaming, and HTTP middleware for authentication, rate limiting, and permission enforcement.

### Event Driven Architecture

The ingestion pipeline runs as a sequence of decoupled asynchronous stages connected through a message broker. Each stage publishes a domain event upon completion. Dedicated workers subscribe to those events and execute the next stage independently.

This design provides:

* Fault isolation: a failure in one worker does not affect others or the retrieval API
* Independent scaling: each worker type can be scaled based on its queue depth
* Broker portability: Redis and Celery can be replaced with Kafka by swapping the Infrastructure queue implementation
* Full traceability: every event carries document and job identifiers, enabling complete processing history reconstruction

---

## Asynchronous Data Pipeline

```
Upload
    |
    v
OCR (PaddleOCR)
    |
    v
Parse and Chunk (Unstructured)
    |
    v
AI Sensitivity Classification
    |
    v
Human Review
    |
    v
Embedding Generation
    |
    v
Vector DB Indexing (Qdrant)
```

**Stage 1: Upload and Initialization**
File hash is computed to reject duplicates. A document record is created in PostgreSQL with status `pending`. A `DocumentUploadedEvent` is published. The API returns immediately.

**Stage 2: OCR**
The OCR worker retrieves the file from storage and processes it through PaddleOCR. Extracted text is persisted. An `OCRCompletedEvent` is published.

**Stage 3: Chunking**
The chunk worker applies Unstructured to segment text by document structure signals (headings, paragraphs, tables, lists) rather than fixed character counts. Each chunk receives a unique ID. A `ChunkCreatedEvent` is published per chunk.

**Stage 4: Sensitivity Classification**
The classification worker applies a sensitivity model to each chunk and assigns a label such as `public`, `internal`, `confidential`, or `restricted`. Chunk status is set to `pending_review`. A `LabelAssignedEvent` is published.

**Stage 5: Human Review**
Authorized reviewers inspect chunk content and AI-assigned labels via the React admin interface. Reviewers may approve, override, or reject. Approval produces a `ReviewApprovedEvent`. Rejection excludes the chunk from indexing permanently.

**Stage 6: Embedding**
The embedding worker generates a vector representation for each approved chunk. The vector is persisted alongside the chunk record. An `EmbeddingCompletedEvent` is published.

**Stage 7: Vector Indexing**
The vector worker inserts the embedding and its metadata (document ID, role permissions, sensitivity label, source reference) into Qdrant. Chunk status is updated to `indexed`.

---

## Technology Stack

* FastAPI for async HTTP and WebSocket handling
* PostgreSQL with SQLAlchemy ORM for relational data and job state
* Qdrant for vector storage and metadata-filtered similarity search
* Redis and Celery for the event-driven worker pipeline
* PaddleOCR for scanned document text extraction
* Unstructured for structure-aware document parsing and chunking
* Prometheus for metrics instrumentation

---

## Directory Structure

```
backend/
    app/
        domain/
            entities/           Core business objects
            enums/              Shared enumerated types
            events/             Domain event definitions
            repositories/       Abstract repository interfaces
        application/
            auth/
            ingestion/
            review/
            retrieval/
            permission/
            jobs/
        infrastructure/
            database/
                postgres/
                    models/
                    repositories/
                migrations/
            vector/
                qdrant/
                milvus/
            queue/
                redis/
                kafka/
            storage/
                local/
                minio/
            parser/
                unstructured/
            ocr/
                paddleocr/
            embedding/
            classifier/
            llm/
        presentation/
            api/
                auth/
                chat/
                documents/
                chunks/
                reviews/
                jobs/
                metrics/
                admin/
            websocket/
            middleware/
        shared/
            config/
            logger/
            security/
            exceptions/
            utils/
    workers/
    consumers/
    scheduler/
    monitoring/
    tests/
        unit/
        integration/
        e2e/
    docker/
    main.py
    requirements.txt
```

---

## Local Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis broker URL | Yes |
| `QDRANT_HOST` | Qdrant hostname | Yes |
| `QDRANT_PORT` | Qdrant port | Yes |
| `OPENAI_API_KEY` | OpenAI API key | No |
| `GROQ_API_KEY` | Groq API key | No |
| `LLM_PROVIDER` | `openai`, `groq`, or `ollama` | Yes |
| `STORAGE_BACKEND` | `local` or `minio` | Yes |
| `RETRIEVAL_TOP_K` | Candidate chunks before rerank (default 15) | No |
| `RERANK_TOP_K` | Final chunks sent to LLM (default 8) | No |

---

## Running Workers

Each worker must be started as a separate process.

```bash
celery -A workers.ingestion_worker worker --loglevel=info
celery -A workers.ocr_worker worker --loglevel=info
celery -A workers.chunk_worker worker --loglevel=info
celery -A workers.classify_worker worker --loglevel=info
celery -A workers.embedding_worker worker --loglevel=info
celery -A workers.vector_worker worker --loglevel=info
```

---

## Operational Notes

**Access control integrity**
The sensitivity label and role permission metadata attached to each chunk at ingestion time directly controls what content users can retrieve. Incorrect metadata set during ingestion cannot be corrected at query time. Audit role-to-label permission mappings in PostgreSQL before enabling retrieval for any role.

**Bootstrap ingestion performance**
Processing large document archives is expected to take multiple days. This is by design. Each stage checkpoints progress in PostgreSQL. Worker restarts resume from the last incomplete stage rather than reprocessing from the beginning.

**CORS in production**
The default CORS configuration allows `localhost:5173` and `localhost:8001`. Add production frontend domains to the allowed origins in `app/shared/config` before deploying.

**Database sessions in workers**
SQLAlchemy sessions used inside Celery workers operate outside the FastAPI request lifecycle. Each task must explicitly acquire and release its own session to prevent connection pool exhaustion.

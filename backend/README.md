# chatRAG: Enterprise Retrieval Augmented Generation Platform

## Table of Contents

* Project Overview
* Context and Objectives
* Architectural Design
* Asynchronous Data Pipeline
* Technology Stack
* Directory Structure
* Environment Configuration
* Deployment Instructions
* Operational Considerations
* Future Development Roadmap

---

## Project Overview

chatRAG is an autonomous, large-scale document ingestion and intelligent retrieval system engineered to serve modern enterprise data environments. The platform integrates a multi-stage processing pipeline with a conversational query interface, enabling organizations to extract structured knowledge from unstructured document repositories and surface that knowledge to authorized users through a context-aware language model interface.

The primary goal of the system is to process massive volumes of enterprise documentation securely, reliably, and with a high degree of operational autonomy. The platform is not designed to optimize for instantaneous throughput. Instead, it is architected to prioritize long-term system stability, data integrity, security compliance, and fault-tolerant operation under sustained high-volume workloads exceeding one terabyte of raw document data.

The platform achieves its objectives through the composition of four principal capabilities. First, it provides an automated ingestion pipeline capable of transforming raw document files into semantically indexed vector representations. Second, it enforces a granular role-based access control model at the data retrieval layer, ensuring that language model responses are generated exclusively from documents the requesting user is authorized to access. Third, it incorporates a human-in-the-loop review mechanism for validating artificial intelligence sensitivity classifications before document content is made available for retrieval. Fourth, it exposes a streaming conversational API that integrates retrieval results with large language model generation in real time.

---

## Context and Objectives

### Organizational Necessity

Enterprise organizations accumulate documentation at a rate and volume that far exceeds the capacity of human knowledge workers to manually index, categorize, or retrieve relevant content on demand. Legal contracts, internal policy documents, technical specifications, research reports, and operational procedures are typically stored in heterogeneous formats across distributed repositories, rendering traditional keyword search systems inadequate for nuanced question-answering tasks.

The introduction of Retrieval Augmented Generation as an architectural pattern addresses this inadequacy by combining the semantic understanding capabilities of large language models with the precision of vector similarity search over a curated and access-controlled document corpus. However, deploying such a system at enterprise scale introduces a distinct set of engineering challenges that this platform is specifically designed to resolve.

### Scalability Requirements

The system must be capable of processing document corpora measured in hundreds of gigabytes to multiple terabytes. Bootstrap ingestion operations, defined as the initial mass processing of an organization's historical document archive, may require multiple days of sustained pipeline execution. The architecture must remain stable and resumable throughout this extended processing window, with the capability to checkpoint progress, recover from partial failures, and retry individual processing stages without reprocessing previously completed work.

Delta ingestion operations, defined as the incremental processing of newly uploaded or modified documents, must be handled independently of bootstrap operations and must not interfere with the availability of the retrieval and query interfaces.

### Security and Access Control Objectives

Document sensitivity classification is a first-class concern within this platform. Every document chunk processed by the pipeline receives an artificial intelligence generated sensitivity label prior to being made available for retrieval. A human review interface allows authorized personnel to validate, override, or reject these classifications before the corresponding content is indexed in the vector store. This human-in-the-loop mechanism ensures that sensitive content is never inadvertently exposed through the retrieval layer due to misclassification.

Access control is enforced at query time by filtering retrieval candidates against the role permissions of the requesting user. A user assigned to a restricted role will only receive language model responses synthesized from document chunks explicitly approved for that role, regardless of the semantic relevance of restricted content to the query.

### Design Philosophy

The platform is deliberately designed to avoid dependency on managed cloud services for its core operational functions. All processing components, including the vector store, the message broker, the relational database, and the language model interface, are deployable in fully self-hosted configurations. This design decision reflects the enterprise requirement for data sovereignty, auditability, and the ability to operate in network-isolated or air-gapped environments. Cloud-hosted alternatives may be substituted by modifying environment configuration variables without altering application code.

---

## Architectural Design

### Clean Architecture

The platform is structured according to the principles of Clean Architecture as articulated by Robert C. Martin. This organizational pattern mandates a strict separation of concerns through concentric layers of abstraction, where each layer is permitted to depend only on layers interior to itself and is explicitly prohibited from depending on outer layers.

The innermost layer is the Domain layer. This layer contains the core business entities, enumerated types, domain events, and repository interface definitions that represent the fundamental concepts of the platform. The Domain layer has zero external dependencies. It does not import from any framework, database library, or infrastructure module. This property ensures that the business logic of the platform remains stable and testable in complete isolation from the technologies used to implement it.

The second layer is the Application layer. This layer contains the use case implementations that orchestrate interactions between domain entities and repository interfaces to fulfill specific business operations. Use cases such as initiating an ingestion job, approving a human review decision, or processing a retrieval query are defined in this layer. The Application layer depends on the Domain layer but remains agnostic to any specific infrastructure implementation.

The third layer is the Infrastructure layer. This layer contains the concrete implementations of all repository interfaces defined in the Domain layer. It provides the actual database access logic, vector store communication, message queue publishing and consumption, file storage operations, optical character recognition execution, document parsing, embedding model inference, and large language model integration. The Infrastructure layer implements interfaces defined in the Domain layer, thereby satisfying the Dependency Inversion Principle.

The outermost layer is the Presentation layer. This layer contains the FastAPI route definitions, request and response schema models, WebSocket handlers, and HTTP middleware. It translates incoming HTTP requests into use case invocations and transforms use case results into HTTP responses. The Presentation layer depends on the Application layer for business logic execution.

This layered architecture provides several material benefits for an enterprise system of this scale. It permits the substitution of infrastructure components, for example replacing Qdrant with Milvus as the vector store, without modifying any domain or application logic. It enables comprehensive unit testing of business logic without requiring live database connections or external service availability. It also allows different development teams to work on domain logic, infrastructure implementations, and API definitions concurrently with minimal merge conflicts.

### Event Driven Architecture

The platform adopts an Event Driven Architecture to manage the execution of its multi-stage ingestion pipeline. In this pattern, each completed processing stage publishes a domain event to a message broker. Dedicated event consumers subscribe to specific event types and execute the subsequent processing stage upon receipt of the corresponding event.

The event topology of the ingestion pipeline is as follows. The completion of a document upload operation produces a DocumentUploadedEvent. The completion of optical character recognition processing produces an OCRCompletedEvent. The completion of text chunking produces a ChunkCreatedEvent. The completion of artificial intelligence sensitivity classification produces a LabelAssignedEvent. The approval of a human review decision produces a ReviewApprovedEvent. The completion of vector embedding generation produces an EmbeddingCompletedEvent.

This event-driven decomposition provides multiple architectural advantages critical to enterprise-scale operation.

* Fault isolation is achieved because the failure of any single processing stage does not propagate to other stages. A failed OCR worker does not affect the embedding worker or the retrieval API. Each worker operates independently and can be restarted without system-wide disruption.
* Horizontal scalability is achieved because each worker type can be scaled independently based on observed queue depth. If optical character recognition is identified as a bottleneck during bootstrap ingestion, additional OCR worker instances can be deployed without modifying any other system component.
* Broker replaceability is achieved because the Redis and Celery combination used in development can be replaced with Apache Kafka in production by substituting the publisher and consumer implementations in the Infrastructure layer. The domain events and application use cases remain unchanged.
* Observability is naturally supported because each event carries a document identifier and a job identifier, enabling the complete processing history of any document to be reconstructed from the event log.

### Worker Pattern

In addition to event-driven consumers, the platform employs dedicated worker processes for computationally intensive tasks. Workers for ingestion, optical character recognition, chunking, classification, review processing, embedding generation, and vector indexing are defined as independent Python modules within the workers directory. This separation allows each worker type to be deployed in a dedicated container with resource allocations appropriate to its computational profile, for example allocating GPU resources exclusively to the embedding worker or the optical character recognition worker.

---

## Asynchronous Data Pipeline

The ingestion pipeline is the foundational data preparation subsystem of the platform. It transforms raw document files into semantically indexed, access-controlled vector representations through a sequence of discrete, asynchronous processing stages.

### Stage One: Document Upload and Initialization

A document upload request is received by the Presentation layer API. The system computes a cryptographic hash of the uploaded file content to detect duplicate submissions. If an identical hash is found in the relational database, the upload is rejected with an appropriate status code to prevent redundant processing. If the hash is novel, a document record is created in PostgreSQL with an initial status of pending, and a DocumentUploadedEvent is published to the message broker. The API returns immediately to the caller without awaiting pipeline completion.

### Stage Two: Optical Character Recognition Processing

The OCR worker subscribes to DocumentUploadedEvents. Upon receipt, it retrieves the document file from the storage layer and submits it to the PaddleOCR processing engine. PaddleOCR is selected for this role due to its strong multilingual support, its open-source license permitting self-hosted deployment, and its demonstrated accuracy on scanned document inputs including low-resolution or degraded source material. Upon completion, the extracted text content is persisted and an OCRCompletedEvent is published.

### Stage Three: Text Extraction and Chunking

The chunk worker subscribes to OCRCompletedEvents. It retrieves the extracted text and applies the Unstructured document parsing library to segment the content into semantically coherent text chunks. Chunk boundaries are determined by document structure signals including heading levels, paragraph breaks, table boundaries, and list demarcations rather than by fixed character counts alone. This structure-aware chunking strategy improves retrieval precision by ensuring that retrieved chunks represent complete semantic units. Each chunk is assigned a unique identifier and associated with its parent document record. A ChunkCreatedEvent is published for each generated chunk.

### Stage Four: Artificial Intelligence Sensitivity Classification

The classification worker subscribes to ChunkCreatedEvents. It applies a sensitivity classification model to each chunk to assign one of a predefined set of sensitivity labels, such as public, internal, confidential, or restricted. The classification model is defined in the Infrastructure layer and may be implemented using a fine-tuned language model, a zero-shot classifier, or a rules-based heuristic depending on the deployment configuration. Upon completion, a LabelAssignedEvent is published and the chunk record is updated in the relational database with the assigned sensitivity label and a status of pending review.

### Stage Five: Human-in-the-Loop Verification

The review worker manages the queue of chunks awaiting human verification. The React administration interface presents pending review items to authorized reviewers, displaying chunk content alongside the artificial intelligence assigned sensitivity label and its confidence score where available. Reviewers may approve the assigned label, override it with an alternative label, or reject the chunk from indexing entirely. An approved decision produces a ReviewApprovedEvent. A rejected decision marks the chunk as excluded and removes it from the processing queue. This verification stage ensures that no content enters the vector index without explicit human authorization.

### Stage Six: Vector Embedding Generation

The embedding worker subscribes to ReviewApprovedEvents. It retrieves the approved chunk content and submits it to the configured embedding model to generate a high-dimensional vector representation. The embedding model is executed locally using the Infrastructure layer embedding module, which may interface with a locally deployed model server or a remotely hosted embedding API depending on configuration. The generated embedding vector is persisted alongside the chunk record and an EmbeddingCompletedEvent is published.

### Stage Seven: Vector Database Storage

The vector worker subscribes to EmbeddingCompletedEvents. It retrieves the embedding vector and associated chunk metadata, including document identifier, role permissions, sensitivity label, and source location, and inserts the record into the Qdrant vector store. The metadata payload stored alongside each vector is specifically designed to support efficient access control filtering at query time. Upon successful insertion, the chunk status is updated to indexed and the ingestion job progress counter is incremented in PostgreSQL.

---

## Technology Stack

### API Gateway

* FastAPI is selected as the HTTP framework for the Presentation layer due to its native support for asynchronous request handling, its automatic OpenAPI documentation generation, its type-safe request and response validation through Pydantic, and its integration with Python asyncio concurrency model. FastAPI streaming response capabilities are utilized by the chat interface to deliver language model output tokens to the client incrementally as they are generated.

### Relational Database

* PostgreSQL serves as the system of record for all document metadata, chunk records, ingestion job state, user and role definitions, access permissions, and human review decisions. PostgreSQL is selected for its maturity, its ACID transaction guarantees, its robust support for complex relational queries, and its extensibility through the pgvector extension, which provides native vector similarity search capabilities as an alternative to a dedicated vector store in lower-scale deployments.

### Message Broker

* Redis combined with the Celery distributed task queue framework serves as the message broker and worker orchestration layer in the development and initial production configuration. Redis is selected for its low operational overhead, its high throughput for queue operations, and its ease of local deployment. The queue abstraction layer is implemented behind a repository interface, permitting migration to Apache Kafka for production deployments requiring persistent event logs, consumer group semantics, or replay capabilities without modifications to business logic.

### Vector Store

* Qdrant is selected as the primary vector database for storing document chunk embeddings. Qdrant is an open-source vector similarity search engine that supports self-hosted deployment, provides native metadata filtering capabilities essential for access control enforcement at query time, and demonstrates performance characteristics suitable for collections of several million vectors without requiring specialized hardware. For deployments exceeding Qdrant practical capacity, the vector store implementation may be replaced with Milvus by substituting the Infrastructure layer repository implementation.

### Document Processing

* PaddleOCR is used for optical character recognition of scanned and image-based document inputs. Unstructured is used for structure-aware text extraction and chunking of parsed document content. Both libraries support local execution without external API dependencies.

### Monitoring and Observability

* Prometheus is integrated for metrics collection across all system components. Grafana is configured to consume Prometheus metrics and provide operational dashboards for monitoring queue depths, worker throughput, ingestion job progress, retrieval latency, and error rates.

### Storage

* Local filesystem storage is used in development configurations. MinIO is used in production configurations to provide S3-compatible object storage for uploaded document files, supporting both on-premises and cloud deployment scenarios.

---

## Directory Structure

The repository is organized according to the Clean Architecture layer hierarchy described above.

```
backend/
    app/
        domain/
            entities/
            enums/
            events/
            repositories/
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

## Environment Configuration

The platform is configured exclusively through environment variables to support the single-codebase, multi-environment deployment model. The following variables must be defined in the `.env` file prior to startup.

* `DATABASE_URL` specifies the PostgreSQL connection string including host, port, database name, username, and password.
* `REDIS_URL` specifies the Redis connection string used by the Celery broker and result backend.
* `QDRANT_HOST` specifies the hostname of the Qdrant vector store instance.
* `QDRANT_PORT` specifies the port of the Qdrant vector store instance.
* `OPENAI_API_KEY` specifies the API key for the OpenAI language model and embedding services when cloud-hosted models are configured.
* `EMBEDDING_MODEL` specifies the identifier of the embedding model to be used for vector generation.
* `LLM_PROVIDER` specifies the language model provider, accepting values of openai, groq, or ollama.
* `STORAGE_BACKEND` specifies the storage provider, accepting values of local or minio.
* `RETRIEVAL_TOP_K` specifies the number of candidate chunks retrieved from the vector store prior to reranking, with a default value of 15.
* `RERANK_TOP_K` specifies the number of chunks retained after the reranking stage for inclusion in the language model prompt, with a default value of 8.

---

## Deployment Instructions

### Local Development

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The development API server will be accessible at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

### Worker Processes

Each worker type must be started as a separate process. The following commands start the Celery workers for each pipeline stage.

```bash
celery -A workers.ingestion_worker worker --loglevel=info
celery -A workers.ocr_worker worker --loglevel=info
celery -A workers.chunk_worker worker --loglevel=info
celery -A workers.classify_worker worker --loglevel=info
celery -A workers.embedding_worker worker --loglevel=info
celery -A workers.vector_worker worker --loglevel=info
```

### Container Deployment

```bash
docker-compose -f docker/docker-compose.yml up --build
```

---

## Operational Considerations

### Ingestion Performance

Bootstrap ingestion of large document archives is expected to require multiple days of sustained processing. This behavior is architecturally intentional. The system prioritizes stability and fault tolerance over throughput velocity. Each processing stage maintains checkpointed state in PostgreSQL, ensuring that a worker restart or infrastructure interruption results in at most one stage of reprocessing per affected document rather than a complete pipeline restart.

### Access Control Integrity

The sensitivity classification and human review pipeline must be treated as a security-critical path. Misconfiguration of role permissions or sensitivity labels at ingestion time may result in the unintended exposure of restricted content through the retrieval interface. Operators are advised to audit the role-to-label permission matrix in the relational database prior to enabling retrieval access for any user role.

### Cross-Origin Resource Sharing

The current CORS configuration permits requests from `http://localhost:5173` and `http://localhost:8001` for local development purposes. Production deployments must extend this configuration to include all authorized frontend origins. Failure to update this configuration will prevent the administration interface from communicating with the API server in production environments.

### Database Session Management

SQLAlchemy session lifecycle management must be handled with care in asynchronous contexts, particularly within worker processes and event consumers that execute outside the FastAPI request lifecycle. Each unit of work must explicitly acquire and release a database session to prevent connection pool exhaustion under sustained load.

---

## Future Development Roadmap

* Migration of the message broker from Redis and Celery to Apache Kafka for production environments requiring event log persistence and consumer group replay capabilities.
* Integration of a dedicated reranking model to improve retrieval precision beyond the baseline vector similarity ranking.
* Implementation of query routing based on detected document domain to reduce retrieval latency and improve result relevance.
* Extension of the human review interface to support batch approval workflows for large document archives.
* Fine-tuning of the sensitivity classification model using validated human review decisions accumulated over time to improve classification accuracy.
* Implementation of document version tracking to support delta ingestion of modified documents without requiring full reprocessing of unchanged content.
* Addition of audit logging for all retrieval queries, including the document chunks returned and the user role that issued the request, to support compliance reporting requirements.

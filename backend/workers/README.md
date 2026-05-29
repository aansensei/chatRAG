## workers

Long-running background processes. Each worker handles one stage of the ingestion pipeline and runs independently alongside the API server.

Each worker receives a message from the queue (Kafka or Redis), processes it, and publishes the next message. A worker crash does not affect other workers.

### Files

`ingestion_worker.py` - orchestrator worker that drives the full pipeline for a document: receives an upload request, calls the other workers in sequence, updates IngestJob status at each step.

`ocr_worker.py` - receives a scanned page image, runs PaddleOCR, returns the extracted text. Uses GPU if available.

`chunk_worker.py` - receives raw text, splits it into chunks using a configured strategy (sentence, paragraph, or token-based). Creates Chunk entities and saves them to the DB.

`embedding_worker.py` - receives a list of chunks, runs the embedding model, returns vectors. Batch-processes chunks to maximize throughput.

`vector_worker.py` - receives embeddings, upserts them into the Qdrant collection. Operation is idempotent — safe to upsert if a chunk already exists.

`classify_worker.py` - receives extracted text, runs the sensitivity classifier, updates Document.sensitivity, and triggers a review if needed.

`review_worker.py` - receives a review decision (approve/reject) and updates the Document status accordingly.

## consumers

Event consumer entry points. Each file subscribes to one domain event and triggers the next step in the pipeline. Each consumer runs as an independent process (or coroutine).

Pipeline event chain:
`DocumentUploaded` → `OcrCompleted` → `ChunkCreated` → `EmbeddingCompleted` → `LabelAssigned` → `ReviewApproved`

### Files

`document_uploaded_handler.py` - receives `DocumentUploaded`, calls the extractor to get raw text. If the document has scanned pages, triggers OCR. Otherwise publishes `ChunkCreated` directly.

`ocr_completed_handler.py` - receives `OcrCompleted`, merges the OCR text into the document, publishes `ChunkCreated`.

`chunk_created_handler.py` - receives `ChunkCreated`, calls the embedding model to vectorize each chunk, publishes `EmbeddingCompleted`.

`embedding_handler.py` - receives `EmbeddingCompleted`, upserts vectors into Qdrant, calls the classifier to assign a sensitivity label, publishes `LabelAssigned`.

`review_handler.py` - receives `LabelAssigned`. If sensitivity >= CONFIDENTIAL, creates a Review and waits. If below CONFIDENTIAL, transitions Document to READY immediately.

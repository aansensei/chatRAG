## domain/events

Domain events — payloads for the message queue. Each event marks that something happened in the pipeline and triggers the next step. Consumers in `consumers/` subscribe to these events.

Pipeline flow in order: document_uploaded → ocr_completed → chunk_created → embedding_completed → label_assigned → review_approved (if required)

### Files

`document_uploaded.py` - document has been saved to storage and is ready for text extraction.

`ocr_completed.py` - OCR finished on scanned pages. Triggers chunking.

`chunk_created.py` - text has been split into chunks. Triggers embedding.

`embedding_completed.py` - all chunks have been vectorized. Triggers indexing into Qdrant.

`label_assigned.py` - sensitivity label has been assigned. If CONFIDENTIAL+, triggers Review creation.

`review_approved.py` - reviewer approved the document. Document transitions to READY.
